from __future__ import annotations

from typing import Any, TypedDict

from apps.src.config import cofig
from apps.src.models.DTO import AnalysisRequest, AnalysisResponse


class ClusterWorkflowState(TypedDict, total=False):
    cluster: dict[str, Any]
    cluster_index: int
    representative_article: dict[str, Any]
    request: AnalysisRequest
    result: AnalysisResponse


class ClusterAnalysisWorkflow:
    """Cluster input orchestration layer with an optional LangGraph backend."""

    def __init__(self, analyzer_service: Any) -> None:
        self._analyzer_service = analyzer_service
        self._graph = self._build_graph() if cofig.USE_LANGGRAPH else None

    def run(self, payload: dict[str, Any] | list[dict[str, Any]]) -> list[AnalysisResponse]:
        clusters = self._coerce_clusters(payload)
        results: list[AnalysisResponse] = []
        total_clusters = len(clusters)

        for index, cluster in enumerate(clusters):
            result = self._run_single_cluster(cluster, index=index, total=total_clusters)
            results.append(result)

        return results

    def _run_single_cluster(self, cluster: dict[str, Any], *, index: int, total: int) -> AnalysisResponse:
        if self._graph is not None:
            final_state = self._graph.invoke({"cluster": cluster, "cluster_index": index})
            result = final_state["result"]
            return self._attach_workflow_debug(result, index=index, total=total, workflow_backend="langgraph")

        representative = self._select_representative({"cluster": cluster, "cluster_index": index})["representative_article"]
        request = self._build_request(
            {"cluster": cluster, "cluster_index": index, "representative_article": representative}
        )["request"]
        result = self._analyze_request({"cluster": cluster, "cluster_index": index, "request": request})["result"]
        return self._attach_workflow_debug(result, index=index, total=total, workflow_backend="sequential")

    def _coerce_clusters(self, payload: dict[str, Any] | list[dict[str, Any]]) -> list[dict[str, Any]]:
        if isinstance(payload, list):
            return payload
        if isinstance(payload, dict) and isinstance(payload.get("clusters"), list):
            return payload["clusters"]
        return [payload]

    def _build_graph(self) -> Any | None:
        try:
            from langgraph.graph import END, START, StateGraph
        except ImportError:
            return None

        builder = StateGraph(ClusterWorkflowState)
        builder.add_node("select_representative", self._select_representative)
        builder.add_node("build_request", self._build_request)
        builder.add_node("analyze_request", self._analyze_request)
        builder.add_edge(START, "select_representative")
        builder.add_edge("select_representative", "build_request")
        builder.add_edge("build_request", "analyze_request")
        builder.add_edge("analyze_request", END)
        return builder.compile()

    def _select_representative(self, state: ClusterWorkflowState) -> dict[str, Any]:
        representative = self._analyzer_service._select_representative_article(state["cluster"])
        return {"representative_article": representative}

    def _build_request(self, state: ClusterWorkflowState) -> dict[str, Any]:
        request = self._analyzer_service._cluster_to_request(
            state["cluster"],
            representative=state.get("representative_article"),
        )
        return {"request": request}

    def _analyze_request(self, state: ClusterWorkflowState) -> dict[str, Any]:
        result = self._analyzer_service.analyze(state["request"])
        return {"result": result}

    def _attach_workflow_debug(
        self,
        result: AnalysisResponse,
        *,
        index: int,
        total: int,
        workflow_backend: str,
    ) -> AnalysisResponse:
        debug = dict(result.debug)
        debug.update(
            {
                "workflow_backend": workflow_backend,
                "cluster_index": index,
                "cluster_total": total,
            }
        )
        return result.model_copy(update={"debug": debug})
