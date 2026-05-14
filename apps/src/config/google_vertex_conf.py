"""Google Cloud Vertex AI 및 Gemini API 설정.

GEMINI_USE_VERTEX=true 시 Vertex AI를 사용하여 Google Cloud 크레딧이 차감됨.
false(기본) 시 Google AI Studio API 키 방식으로 동작.
"""

import os

GEMINI_USE_VERTEX: bool = os.environ.get("GEMINI_USE_VERTEX", "").lower() in ("1", "true", "yes")
GOOGLE_CLOUD_PROJECT: str = os.environ.get("GOOGLE_CLOUD_PROJECT", "")
GOOGLE_CLOUD_LOCATION: str = os.environ.get("GOOGLE_CLOUD_LOCATION", "asia-northeast3")
VERTEX_MODEL: str = os.environ.get("VERTEX_MODEL", "gemini-2.5-flash")
GEMINI_API_KEY: str = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL: str = os.environ.get("LLM_MODEL", "gemini-2.5-flash-lite")
