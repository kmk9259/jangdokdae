from __future__ import annotations

from apps.src.models.DTO import AnalysisRequest, AnalysisResponse
from apps.src.services.analyzer.issue_based_analyzer import IssueBasedAnalyzerService


class AnalyzerService:
    """Analyzer 레이어의 진입점."""

    def __init__(self) -> None:
        self._issue_based_analyzer = IssueBasedAnalyzerService()

    def analyze(self, article: AnalysisRequest) -> AnalysisResponse:
        return self._issue_based_analyzer.analyze(article)
