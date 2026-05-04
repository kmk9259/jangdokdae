from __future__ import annotations

from fastapi import APIRouter

from apps.src.models.DTO import AnalysisRequest, AnalysisResponse
from apps.src.services.analyzer.analyzer_service import AnalyzerService


router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.get("/health")
def analysis_health() -> dict[str, str]:
    return {"status": "ok", "service": "analyzer"}


@router.post("/analyze", response_model=AnalysisResponse)
def analyze_article(request: AnalysisRequest) -> AnalysisResponse:
    service = AnalyzerService()
    return service.analyze(request)
