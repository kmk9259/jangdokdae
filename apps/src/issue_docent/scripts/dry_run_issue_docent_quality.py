import argparse
import asyncio
import json
from pathlib import Path
from typing import Any

from apps.src.config.database import AsyncSessionLocal
from apps.src.repositories.issue_docent import IssueDocentRepository
from apps.src.services.issue_docent.generation_service import IssueDocentGenerationService


REQUIRED_MANUAL_GATES = [
    "output_quality",
    "prompt_quality",
    "beginner_difficulty",
    "central_article_reflection",
    "concision",
]


def build_quality_review_row(
    *,
    cluster_id: int,
    title: str,
    teaser: str,
    summary: str,
) -> dict[str, Any]:
    return {
        "cluster_id": cluster_id,
        "title": title,
        "teaser": teaser,
        "summary": summary,
        "paragraph_count": len([part for part in summary.split("\n\n") if part.strip()]),
        "manual_gates": {gate: "UNREVIEWED" for gate in REQUIRED_MANUAL_GATES},
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Dry-run Issue Docent quality review.")
    parser.add_argument("--cluster-id", type=int, action="append", required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


async def main() -> None:
    args = parse_args()
    rows: list[dict[str, Any]] = []
    async with AsyncSessionLocal() as session:
        service = IssueDocentGenerationService(IssueDocentRepository(session))
        for cluster_id in args.cluster_id:
            result = await service.generate_for_cluster(cluster_id, force=True, dry_run=True)
            if result.payload is None:
                raise RuntimeError(f"cluster {cluster_id} did not produce payload")
            rows.append(
                build_quality_review_row(
                    cluster_id=cluster_id,
                    title=result.payload.title,
                    teaser=result.payload.teaser,
                    summary=result.payload.summary,
                )
            )
    args.output.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    asyncio.run(main())
