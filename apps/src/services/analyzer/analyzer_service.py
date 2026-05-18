from __future__ import annotations

from typing import Any

from apps.src.models.DTO import (
    AnalysisRequest,
    AnalysisResponse,
    ArticleMetadata,
    CompanyContextRecord,
    MarketIndicatorRecord,
    SectorContextRecord,
    SidebarContext,
    StructuredContext,
)
from apps.src.services.analyzer.db_cluster_loader import load_cluster_payload_from_db
from apps.src.services.analyzer.issue_based_analyzer import IssueBasedAnalyzerService
from apps.src.services.analyzer.workflow import ClusterAnalysisWorkflow


# 읽는 순서:
# 1) analyze_clusters / analyze_cluster
# 2) _select_representative_article
# 3) _cluster_to_request
# 4) _build_cluster_context
class ClusterAnalyzerService:
    """클러스터 payload를 analyzer 표준 입력으로 바꾸는 중간 계층."""

    def __init__(self) -> None:
        self._issue_based_analyzer = IssueBasedAnalyzerService()

    def analyze(self, article: AnalysisRequest) -> AnalysisResponse:
        """정리된 request를 실제 analyzer로 넘긴다."""
        return self._issue_based_analyzer.analyze(article)

    def analyze_request(self, article: AnalysisRequest) -> AnalysisResponse:
        return self.analyze(article)

    def analyze_cluster(self, payload: dict[str, Any] | AnalysisRequest) -> AnalysisResponse:
        if isinstance(payload, AnalysisRequest):
            return self.analyze_request(payload)

        if self._is_cluster_batch_payload(payload):
            clusters = payload["clusters"]
            if len(clusters) != 1:
                raise ValueError("analyze_cluster()는 클러스터 1개만 받습니다. 여러 개면 analyze_clusters()를 사용하세요.")
            return self.analyze_clusters(payload)[0]

        if not self._is_cluster_payload(payload):
            raise ValueError("Analyzer는 cluster payload만 받습니다.")

        return self.analyze_clusters(payload)[0]

    def analyze_cluster_from_db(self, cluster_id: str) -> AnalysisResponse:
        """DB 클러스터 1개를 읽어 대표 기사 기준 분석 결과로 바꾼다."""
        payload = load_cluster_payload_from_db(cluster_id)
        return self.analyze_cluster(payload)

    def build_sidebar_context(self, payload: dict[str, Any] | AnalysisRequest) -> SidebarContext:
        """같은 입력에서 sidebar용 정형 데이터만 별도로 만든다."""
        article = self.to_analysis_request(payload)
        return self._issue_based_analyzer.build_sidebar_context(article)

    def build_sidebar_context_from_db(self, cluster_id: str) -> SidebarContext:
        payload = load_cluster_payload_from_db(cluster_id)
        return self.build_sidebar_context(payload)

    def analyze_clusters(self, payload: dict[str, Any] | list[dict[str, Any]]) -> list[AnalysisResponse]:
        """클러스터 입력을 workflow 순서대로 돌려 분석 결과 리스트를 만든다."""
        workflow = ClusterAnalysisWorkflow(self)
        return workflow.run(payload)


    def to_analysis_requests(self, payload: dict[str, Any] | list[dict[str, Any]]) -> list[AnalysisRequest]:
        """클러스터 입력을 AnalysisRequest 리스트로 정규화한다."""
        if isinstance(payload, list):
            return [self._cluster_to_request(item) for item in payload]

        if self._is_cluster_batch_payload(payload):
            return [self._cluster_to_request(cluster) for cluster in payload["clusters"]]

        if not self._is_cluster_payload(payload):
            raise ValueError("Analyzer는 cluster payload만 받습니다.")

        return [self._cluster_to_request(payload)]

    def to_analysis_request(self, payload: dict[str, Any] | AnalysisRequest) -> AnalysisRequest:
        """단일 클러스터 입력 1개를 AnalysisRequest로 맞춘다."""
        if isinstance(payload, AnalysisRequest):
            return payload

        if not isinstance(payload, dict):
            raise TypeError("Analyzer input payload must be a dict or AnalysisRequest.")

        if self._is_cluster_payload(payload):
            return self._cluster_to_request(payload)

        if self._is_cluster_batch_payload(payload):
            clusters = payload["clusters"]
            if not clusters:
                raise ValueError("clusters payload is empty.")
            if len(clusters) > 1:
                raise ValueError("Multiple clusters detected. Use analyze_clusters() for batch input.")
            return self._cluster_to_request(clusters[0])

        raise ValueError("Analyzer는 cluster payload만 받습니다.")

    def _is_cluster_batch_payload(self, payload: Any) -> bool:
        return isinstance(payload, dict) and isinstance(payload.get("clusters"), list)

    def _is_cluster_payload(self, payload: Any) -> bool:
        if not isinstance(payload, dict):
            return False
        if "representative_article" in payload:
            return True
        if isinstance(payload.get("cluster"), dict):
            return True
        if isinstance(payload.get("news"), list):
            return True
        return bool(payload.get("representative_news_id"))

    def _cluster_to_request(
        self,
        cluster: dict[str, Any],
        representative: dict[str, Any] | None = None,
    ) -> AnalysisRequest:
        """대표 기사 본문을 중심으로 LLM 입력 1개를 만든다."""
        representative = representative or self._select_representative_article(cluster)
        cluster_meta = cluster.get("cluster") if isinstance(cluster.get("cluster"), dict) else {}
        summary_hint = self._build_cluster_summary_hints(cluster, representative)
        title = representative.get("title") or representative.get("news_title")
        source_titles = self._collect_cluster_titles(cluster)

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
            title=title,
            summary_hint=summary_hint,
            content=representative.get("content") or representative.get("news_content") or "",
            cluster_id=self._extract_cluster_id(cluster),
            cluster_size=self._extract_cluster_size(cluster),
            source_titles=source_titles or ([title] if title else []),
            metadata=ArticleMetadata(
                company_names=self._extract_company_names(cluster, representative),
                sectors=self._coerce_list(
                    cluster.get("sectors")
                    or cluster.get("sector")
                    or cluster.get("cluster_sector")
                    or cluster_meta.get("sectors")
                    or cluster_meta.get("sector")
                    or cluster_meta.get("cluster_sector")
                    or representative.get("sectors")
                    or representative.get("sector")
                ),
                keywords=self._coerce_list(
                    cluster.get("keywords")
                    or cluster.get("keyword")
                    or cluster.get("cluster_keywords")
                    or cluster_meta.get("keywords")
                    or cluster_meta.get("keyword")
                    or cluster_meta.get("cluster_keywords")
                    or representative.get("keywords")
                    or representative.get("keyword")
                ),
            ),
            context=self._build_cluster_context(cluster, representative),
        )

    def _select_representative_article(self, cluster: dict[str, Any]) -> dict[str, Any]:
        """클러스터 안 기사들 중 분석 기준이 될 대표 기사 1개를 고른다."""
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
                candidate_id = str(item.get("id") or item.get("news_id") or item.get("article_id") or "").strip()
                if candidate_id == str(target_id):
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
        cluster_meta = cluster.get("cluster") if isinstance(cluster.get("cluster"), dict) else {}
        company_ids = {
            str(item).strip()
            for item in self._coerce_list(cluster.get("company_ids") or cluster_meta.get("company_ids"))
        }
        if isinstance(cluster_company_context, list):
            collected = [
                item.get("company_name") or item.get("name")
                for item in cluster_company_context
                if isinstance(item, dict)
                and (item.get("company_name") or item.get("name"))
                and (not company_ids or str(item.get("id") or "").strip() in company_ids)
            ]
            if collected:
                return self._coerce_list(collected)

        return []

    def _build_cluster_context(self, cluster: dict[str, Any], representative: dict[str, Any]) -> StructuredContext:
        """회사/섹터/시장 데이터를 StructuredContext로 묶는다."""
        companies = self._build_company_context(cluster)
        sectors = self._build_sector_context(cluster)
        market_indicators = self._build_market_indicators(cluster)
        return StructuredContext(
            companies=companies,
            sectors=sectors,
            market_indicators=market_indicators,
        )

    def _build_company_context(self, cluster: dict[str, Any]) -> list[CompanyContextRecord]:
        company_rows = cluster.get("company")
        if not isinstance(company_rows, list):
            return []

        records: list[CompanyContextRecord] = []
        seen: set[str] = set()
        for row in company_rows:
            if not isinstance(row, dict):
                continue
            name = row.get("company_name") or row.get("name")
            if not name:
                continue
            key = str(name).strip()
            if not key or key in seen:
                continue
            seen.add(key)
            metrics = self._extract_metrics(
                row,
                [
                    "current_price",
                    "price",
                    "close_price",
                    "price_change",
                    "price_change_pct",
                    "volume",
                    "market_cap",
                    "financial_year",
                    "revenue",
                    "revenue_yoy_pct",
                    "operating_income",
                    "operating_income_yoy_pct",
                    "net_income",
                    "net_income_yoy_pct",
                ],
            )
            records.append(
                CompanyContextRecord(
                    name=key,
                    relation="direct",
                    ticker=self._first_text(row.get("ticker"), row.get("stock_code"), row.get("company_code")),
                    sector=self._first_text(row.get("sector")),
                    metrics=metrics,
                )
            )
        return records

    def _build_sector_context(self, cluster: dict[str, Any]) -> list[SectorContextRecord]:
        names = self._coerce_list(cluster.get("sectors") or cluster.get("sector"))
        return [SectorContextRecord(name=name, relation="direct") for name in names if name]

    def _build_market_indicators(self, cluster: dict[str, Any]) -> list[MarketIndicatorRecord]:
        raw_items = cluster.get("market_context")
        if not isinstance(raw_items, list):
            return []

        records: list[MarketIndicatorRecord] = []
        seen: set[str] = set()
        for row in raw_items:
            if not isinstance(row, dict):
                continue
            name = self._first_text(row.get("name"), row.get("indicator_name"), row.get("market_name"))
            if not name:
                continue
            if name in seen:
                continue
            seen.add(name)
            records.append(
                MarketIndicatorRecord(
                    name=name,
                    value=self._first_text(
                        row.get("value"),
                        row.get("current"),
                        row.get("close"),
                        row.get("index_level"),
                        row.get("level"),
                    ),
                    change=self._first_text(
                        row.get("change_pct"),
                        row.get("change"),
                        row.get("rate"),
                        row.get("delta_pct"),
                    ),
                )
            )
        return records

    def _build_cluster_summary_hints(self, cluster: dict[str, Any], representative: dict[str, Any]) -> list[str]:
        hints = []
        hints.extend(self._coerce_list(cluster.get("summary_hint")))
        hints.extend(self._coerce_list(representative.get("summary_hint")))
        titles = self._collect_cluster_titles(cluster)
        if titles:
            hints.append(f"관련 기사 수: {len(titles)}")
        return self._dedupe_strings(hints)

    def _collect_cluster_titles(self, cluster: dict[str, Any]) -> list[str]:
        news_items = cluster.get("news")
        if not isinstance(news_items, list):
            return []
        titles = []
        for item in news_items:
            if not isinstance(item, dict):
                continue
            title = self._first_text(item.get("title"), item.get("news_title"))
            if title:
                titles.append(title)
        return self._dedupe_strings(titles)

    def _extract_cluster_id(self, cluster: dict[str, Any]) -> str | None:
        cluster_meta = cluster.get("cluster") if isinstance(cluster.get("cluster"), dict) else {}
        return self._first_text(
            cluster.get("cluster_id"),
            cluster_meta.get("cluster_id"),
            cluster_meta.get("id"),
        )

    def _extract_cluster_size(self, cluster: dict[str, Any]) -> int | None:
        cluster_meta = cluster.get("cluster") if isinstance(cluster.get("cluster"), dict) else {}
        candidates = [
            cluster.get("cluster_size"),
            cluster_meta.get("size"),
            cluster_meta.get("cluster_size"),
        ]
        for value in candidates:
            if value is None:
                continue
            try:
                return int(value)
            except (TypeError, ValueError):
                continue
        news_items = cluster.get("news")
        if isinstance(news_items, list):
            return len(news_items)
        return None

    def _extract_metrics(self, row: dict[str, Any], keys: list[str]) -> dict[str, str]:
        metrics: dict[str, str] = {}
        for key in keys:
            value = row.get(key)
            if value is None:
                continue
            text = str(value).strip()
            if text:
                metrics[key] = text
        return metrics

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

    def _first_text(self, *values: Any) -> str | None:
        for value in values:
            if value is None:
                continue
            text = str(value).strip()
            if text:
                return text
        return None

    def _dedupe_strings(self, values: list[str]) -> list[str]:
        seen: set[str] = set()
        deduped: list[str] = []
        for value in values:
            key = str(value).strip()
            if not key or key in seen:
                continue
            seen.add(key)
            deduped.append(key)
        return deduped
