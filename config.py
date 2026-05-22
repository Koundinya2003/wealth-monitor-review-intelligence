"""Central configuration and path resolution."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

APP_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = APP_ROOT / "data"
OUTPUT_DIR = APP_ROOT / "output"
REVIEWS_CSV = DATA_DIR / "reviews.csv"
WEEKLY_PULSE_MD = OUTPUT_DIR / "weekly_pulse.md"
WEEKLY_PULSE_PDF = OUTPUT_DIR / "weekly_pulse.pdf"
EMAIL_DRAFT_MD = OUTPUT_DIR / "email_draft.md"
SENTIMENT_CHART = OUTPUT_DIR / "sentiment_chart.png"
ANALYSIS_JSON = OUTPUT_DIR / "analysis.json"

load_dotenv(APP_ROOT / ".env")


def weeks_lookback() -> int:
    raw = int(os.getenv("WEEKS_LOOKBACK", "10"))
    return max(8, min(12, raw))


def openai_model() -> str:
    return os.getenv("OPENAI_MODEL", "gpt-4o")


def app_name() -> str:
    return os.getenv("APP_NAME", "Wealth Monitor")


def google_play_app_id() -> str:
    return os.getenv("GOOGLE_PLAY_APP_ID", "").strip()


def apple_app_id() -> str:
    return os.getenv("APPLE_APP_ID", "").strip()


def apple_country() -> str:
    return os.getenv("APPLE_COUNTRY", "us").strip().lower()


def use_sample_data() -> bool:
    return os.getenv("USE_SAMPLE_DATA", "false").lower() in ("1", "true", "yes")


def ensure_dirs() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
