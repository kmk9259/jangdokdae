from datetime import date, datetime

import pytest

from apps.src.repositories.issue_docent import ArticleForGeneration, ClusterGenerationContext
from apps.src.schemas.issue_docent_llm import (
    ArticleBriefOutput,
    IssueDocentContentOutput,
    IssueDocentContentPlanOutput,
    IssueDocentPlanParagraph,
    QuizOutput,
)
from apps.src.services.issue_docent.generation_service import IssueDocentGenerationService


class FakeRepository:
    class Session:
        async def rollback(self) -> None:
            return None

    session = Session()

    async def get_cluster_context(self, cluster_id: int):
        return ClusterGenerationContext(
            cluster_id=cluster_id,
            run_date=date(2026, 5, 20),
            cluster_seq=1,
            size=1,
            is_singleton=True,
            created_at=datetime(2026, 5, 20),
            company_names=["삼성전자"],
            sectors=["반도체"],
            keywords=["실적"],
            articles=[
                ArticleForGeneration(
                    article_pk=1,
                    article_id="a1",
                    article_order=0,
                    title="삼성전자 실적 기사",
                    url="https://example.com",
                    press="신문",
                    published_date=datetime(2026, 5, 20),
                    content="본문",
                    similarity_to_centroid=1.0,
                )
            ],
        )

    async def get_stock_terms(self):
        return []


class FakeLLMClient:
    async def generate_article_brief(self, article):
        return ArticleBriefOutput(
            article_pk=article.article_pk,
            article_id=article.article_id,
            article_order=article.article_order,
            brief="삼성전자가 실적을 발표했다.",
            core_event="삼성전자가 실적을 발표했다.",
            key_numbers=[],
            stated_background=[],
            stated_market_reactions=[],
            stated_interpretations=[],
            low_priority_details=[],
        )

    async def generate_content_plan(self, *, cluster, article_briefs):
        return IssueDocentContentPlanOutput(
            central_article_order=0,
            central_issue="삼성전자 실적 발표",
            selected_article_orders=[0],
            omitted_article_orders=[],
            paragraphs=[
                IssueDocentPlanParagraph(
                    section="fact",
                    source_article_orders=[0],
                    facts=["삼성전자가 실적을 발표했다."],
                )
            ],
        )

    async def generate_issue_docent_content(self, *, cluster, article_briefs, content_plan):
        return IssueDocentContentOutput(
            title="삼성전자가 실적을 발표했습니다",
            teaser="삼성전자가 실적을 발표했습니다.",
            summary="삼성전자가 실적을 발표했습니다.",
        )

    async def generate_quizzes(self, *, summary, term_candidates):
        return QuizOutput.model_validate_with_term_candidates(
            {
                "quizzes": [
                    {
                        "kind": "issue",
                        "question": "무슨 일이 있었나요?",
                        "options": ["A", "B", "C", "D"],
                        "answer_index": 0,
                        "explanation": "해설",
                    },
                    {
                        "kind": "issue",
                        "question": "본문에 나온 내용은?",
                        "options": ["A", "B", "C", "D"],
                        "answer_index": 1,
                        "explanation": "해설",
                    },
                ]
            },
            has_term_candidates=False,
        )


@pytest.mark.asyncio
async def test_generation_service_dry_run_returns_payload_for_quality_review():
    service = IssueDocentGenerationService(FakeRepository(), llm_client=FakeLLMClient())

    result = await service.generate_for_cluster(1, dry_run=True)

    assert result.status == "dry_run"
    assert result.title == "삼성전자가 실적을 발표했습니다"
    assert result.payload is not None
    assert result.payload.summary == "삼성전자가 실적을 발표했습니다."
