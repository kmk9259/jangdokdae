from apps.src.issue_docent.scripts.dry_run_issue_docent_quality import build_quality_review_row


def test_build_quality_review_row_includes_required_manual_gates():
    row = build_quality_review_row(
        cluster_id=1,
        title="KB자산운용 ETF 순자산이 커졌습니다",
        teaser="KB자산운용의 ETF 순자산이 연초보다 늘었습니다.",
        summary="첫 문단입니다.\n\n둘째 문단입니다.",
    )

    assert row["cluster_id"] == 1
    assert row["manual_gates"] == {
        "output_quality": "UNREVIEWED",
        "prompt_quality": "UNREVIEWED",
        "beginner_difficulty": "UNREVIEWED",
        "central_article_reflection": "UNREVIEWED",
        "concision": "UNREVIEWED",
    }
    assert row["paragraph_count"] == 2
