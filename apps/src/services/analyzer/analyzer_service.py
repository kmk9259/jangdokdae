from __future__ import annotations

from typing import Any

from apps.src.models.DTO import AnalysisRequest, AnalysisResponse, ArticleMetadata
from apps.src.services.analyzer.issue_based_analyzer import IssueBasedAnalyzerService


class AnalyzerService:
    """Analyzer 레이어의 진입점."""

    def __init__(self) -> None:
        self._issue_based_analyzer = IssueBasedAnalyzerService()

    def analyze(self, article: AnalysisRequest) -> AnalysisResponse:
        return self._issue_based_analyzer.analyze(article)

    def analyze_payload(self, payload: dict[str, Any] | AnalysisRequest) -> AnalysisResponse:
        request = self.to_analysis_request(payload)
        return self.analyze(request)

    def analyze_many(self, payload: dict[str, Any] | list[dict[str, Any]]) -> list[AnalysisResponse]:
        from apps.src.services.analyzer.workflow import ClusterAnalysisWorkflow

        workflow = ClusterAnalysisWorkflow(self)
        return workflow.run(payload)

    def to_analysis_requests(self, payload: dict[str, Any] | list[dict[str, Any]]) -> list[AnalysisRequest]:
        if isinstance(payload, list):
            return [self.to_analysis_request(item) for item in payload]

        if isinstance(payload, dict) and isinstance(payload.get("clusters"), list):
            return [self._cluster_to_request(cluster) for cluster in payload["clusters"]]

        return [self.to_analysis_request(payload)]

    def to_analysis_request(self, payload: dict[str, Any] | AnalysisRequest) -> AnalysisRequest:
        if isinstance(payload, AnalysisRequest):
            return payload

        if not isinstance(payload, dict):
            raise TypeError("Analyzer input payload must be a dict or AnalysisRequest.")

        if "representative_article" in payload:
            return self._cluster_to_request(payload)

        if isinstance(payload.get("clusters"), list):
            clusters = payload["clusters"]
            if not clusters:
                raise ValueError("clusters payload is empty.")
            return self._cluster_to_request(clusters[0])

        return self._article_to_request(payload)

    def _article_to_request(self, payload: dict[str, Any]) -> AnalysisRequest:
        company_names = self._coerce_list(payload.get("company_names") or payload.get("company"))
        sectors = self._coerce_list(payload.get("sectors") or payload.get("sector"))
        keywords = self._coerce_list(payload.get("keywords") or payload.get("keyword"))
        summary_hint = self._coerce_list(payload.get("summary_hint"))

        article_id = self._coerce_id(
            payload.get("article_id"),
            payload.get("news_id"),
            payload.get("article_idx"),
        )
        title = payload.get("title") or payload.get("news_title")
        content = payload.get("content") or payload.get("news_content")

        return AnalysisRequest(
            article_id=article_id,
            title=title,
            summary_hint=summary_hint,
            content=content or "",
            metadata=ArticleMetadata(
                company_names=company_names,
                sectors=sectors,
                keywords=keywords,
            ),
        )

    def _cluster_to_request(
        self,
        cluster: dict[str, Any],
        representative: dict[str, Any] | None = None,
    ) -> AnalysisRequest:
        representative = representative or self._select_representative_article(cluster)
        cluster_meta = cluster.get("cluster") if isinstance(cluster.get("cluster"), dict) else {}
        summary_hint = self._build_cluster_summary_hints(cluster, representative)

        return AnalysisRequest(
            article_id=self._coerce_id(
                representative.get("article_id"),
                representative.get("news_id"),
                representative.get("id"),
                representative.get("article_idx"),
                cluster_meta.get("id"),
                cluster_meta.get("cluster_id"),
                cluster.get("cluster_id"),
            ),
            title=representative.get("title") or representative.get("news_title"),
            summary_hint=summary_hint,
            content=representative.get("content") or representative.get("news_content") or "",
            metadata=ArticleMetadata(
                company_names=self._extract_company_names(cluster, representative),
                sectors=self._coerce_list(
                    cluster.get("sectors")
                    or cluster.get("sector")
                    or cluster_meta.get("sectors")
                    or cluster_meta.get("sector")
                    or representative.get("sectors")
                    or representative.get("sector")
                ),
                keywords=self._coerce_list(
                    cluster.get("keywords")
                    or cluster.get("keyword")
                    or cluster_meta.get("keywords")
                    or cluster_meta.get("keyword")
                    or representative.get("keywords")
                    or representative.get("keyword")
                ),
            ),
        )

    def _select_representative_article(self, cluster: dict[str, Any]) -> dict[str, Any]:
        representative = cluster.get("representative_article")
        if isinstance(representative, dict) and representative:
            return representative

        news_items = cluster.get("news")
        if not isinstance(news_items, list) or not news_items:
            return {}

        cluster_meta = cluster.get("cluster") if isinstance(cluster.get("cluster"), dict) else {}
        target_id = (
            cluster.get("representative_news_id")
            or cluster_meta.get("representative_news_id")
            or cluster.get("news_id")
        )

        if target_id:
            for item in news_items:
                if not isinstance(item, dict):
                    continue
                if str(item.get("id") or item.get("news_id") or item.get("article_id") or "").strip() == str(target_id):
                    return item

        for item in news_items:
            if isinstance(item, dict) and item.get("article_role") == "representative":
                return item

        return next((item for item in news_items if isinstance(item, dict)), {})

    def _extract_company_names(self, cluster: dict[str, Any], representative: dict[str, Any]) -> list[str]:
        representative_companies = self._coerce_list(
            representative.get("companies")
            or representative.get("company")
            or representative.get("company_names")
        )
        if representative_companies:
            return representative_companies

        cluster_company_context = cluster.get("company") or []
        if isinstance(cluster_company_context, list):
            collected = [
                item.get("company_name") or item.get("name")
                for item in cluster_company_context
                if isinstance(item, dict) and (item.get("company_name") or item.get("name"))
            ]
            if collected:
                return self._coerce_list(collected)

        return []

    def _build_cluster_summary_hints(self, cluster: dict[str, Any], representative: dict[str, Any]) -> list[str]:
        hints = self._coerce_list(cluster.get("summary_hint"))
        if hints:
            return hints

        candidate_hints = []
        candidate_hints.extend(self._coerce_list(representative.get("media_end_summary")))
        candidate_hints.extend(self._coerce_list(representative.get("keywords")))

        for news_item in cluster.get("news") or []:
            if not isinstance(news_item, dict):
                continue
            title = str(news_item.get("title") or "").strip()
            if title:
                candidate_hints.append(title)
            if len(candidate_hints) >= 4:
                break

        deduped: list[str] = []
        for hint in candidate_hints:
            if hint and hint not in deduped:
                deduped.append(hint)
        return deduped[:4]

    def _coerce_id(self, *values: Any) -> str:
        for value in values:
            if value is None:
                continue
            text = str(value).strip()
            if text:
                return text
        raise ValueError("article_id/news_id/article_idx among input payload is required.")

    def _coerce_list(self, value: Any) -> list[str]:
        if value is None:
            return []
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        text = str(value).strip()
        return [text] if text else []
