from __future__ import annotations

import json
from pathlib import Path

from apps.src.config import cofig
from apps.src.services.analyzer.analyzer_service import AnalyzerService


def main() -> None:
    example_path = Path(__file__).resolve().parents[2] / "docs" / "analysis_cluster_input.json"
    with example_path.open(encoding="utf-8") as handle:
        payload = json.load(handle)

    missing = []
    if cofig.GEMINI_USE_VERTEX and not cofig.GOOGLE_CLOUD_PROJECT:
        missing.append("GOOGLE_CLOUD_PROJECT")
    if not cofig.GEMINI_USE_VERTEX and not cofig.GEMINI_API_KEY:
        missing.append("GEMINI_API_KEY")

    if missing:
        raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")

    service = AnalyzerService()
    results = service.analyze_many(payload)
    print(json.dumps([result.model_dump() for result in results], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
