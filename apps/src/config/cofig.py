from __future__ import annotations

import os

from dotenv import load_dotenv


load_dotenv()


GEMINI_USE_VERTEX = os.getenv("GEMINI_USE_VERTEX", "true").lower() == "true"
GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT")
GOOGLE_CLOUD_LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "asia-northeast3")
VERTEX_MODEL = os.getenv("VERTEX_MODEL", "gemini-2.5-flash")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
USE_LANGCHAIN = os.getenv("USE_LANGCHAIN", "true").lower() == "true"
USE_LANGGRAPH = os.getenv("USE_LANGGRAPH", "true").lower() == "true"
