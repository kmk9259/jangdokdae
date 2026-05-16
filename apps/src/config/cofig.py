from __future__ import annotations

import os

from dotenv import load_dotenv


load_dotenv()


GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
DATABASE_URL = os.getenv("DATABASE_URL")
KIS_APP_KEY = os.getenv("KIS_APP_KEY")
KIS_APP_SECRET = os.getenv("KIS_APP_SECRET")
KIS_BASE_URL = os.getenv("KIS_BASE_URL", "https://openapi.koreainvestment.com:9443")
KIS_TIMEOUT_SEC = float(os.getenv("KIS_TIMEOUT_SEC", "3"))
YAHOO_TIMEOUT_SEC = float(os.getenv("YAHOO_TIMEOUT_SEC", "3"))
