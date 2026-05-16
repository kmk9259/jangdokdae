from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


PointType = Literal["시장반응", "원인", "리스크", "리스크완화", "성장근거", "전망", "핵심수치"]
IssueLayer = Literal["주요 이슈", "직접 촉발 이슈", "시장 해석 이슈", "중장기 전망 이슈"]
IssueType = Literal["시장반응", "원인", "해석", "전망", "리스크", "성장논리", "핵심수치"]


class ArticleMetadata(BaseModel):
    company_names: list[str] = Field(default_factory=list)
    sectors: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)


class CompanyContextRecord(BaseModel):
    name: str
    relation: str = "mentioned"
    ticker: str | None = None
    sector: str | None = None
    metrics: dict[str, str] = Field(default_factory=dict)


class SectorContextRecord(BaseModel):
    name: str
    relation: str = "mentioned"
    metrics: dict[str, str] = Field(default_factory=dict)


class MarketIndicatorRecord(BaseModel):
    name: str
    value: str | None = None
    change: str | None = None


class StructuredContext(BaseModel):
    companies: list[CompanyContextRecord] = Field(default_factory=list)
    sectors: list[SectorContextRecord] = Field(default_factory=list)
    market_indicators: list[MarketIndicatorRecord] = Field(default_factory=list)


class AnalysisRequest(BaseModel):
    article_id: str
    title: str | None = None
    summary_hint: list[str] = Field(default_factory=list)
    content: str = Field(min_length=20)
    metadata: ArticleMetadata = Field(default_factory=ArticleMetadata)
    cluster_id: str | None = None
    cluster_size: int | None = None
    source_titles: list[str] = Field(default_factory=list)
    context: StructuredContext = Field(default_factory=StructuredContext)


class AnalysisSection(BaseModel):
    title: str
    summary: str


class LLMAnalysisResponse(BaseModel):
    article_id: str
    summary: str
    selected_issue_candidates: list[str] = Field(default_factory=list)
    issue_selection_reason: str | None = None
    summary_points: list[str] = Field(default_factory=list)
    evidence_sentences: list[str] = Field(default_factory=list)
    analysis_sections: list[AnalysisSection] = Field(default_factory=list)
    risk_factors: list[str] = Field(default_factory=list)
    opportunity_factors: list[str] = Field(default_factory=list)


class RelatedCompanyCard(BaseModel):
    name: str
    ticker: str | None = None
    sector: str | None = None
    current_price: str | None = None
    price_change_pct: str | None = None


class RelatedMarketCard(BaseModel):
    name: str
    value: str | None = None
    change_pct: str | None = None


class KeyMetric(BaseModel):
    label: str
    value: str
    emphasis: str | None = None


class SidebarContext(BaseModel):
    related_companies: list[RelatedCompanyCard] = Field(default_factory=list)
    related_markets: list[RelatedMarketCard] = Field(default_factory=list)
    key_metrics: list[KeyMetric] = Field(default_factory=list)


class AnalysisSummary(BaseModel):
    summary: str | None = None
    selected_issue_candidates: list[str] = Field(default_factory=list)
    issue_selection_reason: str | None = None
    summary_points: list[str] = Field(default_factory=list)
    evidence_sentences: list[str] = Field(default_factory=list)
    analysis_sections: list[AnalysisSection] = Field(default_factory=list)
    risk_factors: list[str] = Field(default_factory=list)
    opportunity_factors: list[str] = Field(default_factory=list)


class AnalysisResponse(BaseModel):
    cluster_id: str | None = None
    analysis_summary: AnalysisSummary = Field(default_factory=AnalysisSummary)
    market_context: StructuredContext = Field(default_factory=StructuredContext)
    sidebar_context: SidebarContext = Field(default_factory=SidebarContext)
