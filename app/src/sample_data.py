"""Explicitly marked sample reviews for demo/offline runs."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pandas as pd

# DEMO/SAMPLE DATA — not from live stores
SAMPLE_REVIEWS: list[dict] = [
    {
        "store": "google_play",
        "review_id": "sample-gp-001",
        "rating": 5,
        "title": "Great net worth tracking",
        "review_text": "Easy onboarding and my portfolios synced within minutes. Love the weekly snapshot.",
        "review_date": (datetime.now(timezone.utc) - timedelta(days=12)).isoformat(),
    },
    {
        "store": "google_play",
        "review_id": "sample-gp-002",
        "rating": 2,
        "title": "Crashes after update",
        "review_text": "App freezes when I open transactions. Performance was fine last month.",
        "review_date": (datetime.now(timezone.utc) - timedelta(days=25)).isoformat(),
    },
    {
        "store": "apple_app_store",
        "review_id": "sample-as-001",
        "rating": 4,
        "title": "Clean UI",
        "review_text": "Dashboard is intuitive but notifications are too frequent for price alerts.",
        "review_date": (datetime.now(timezone.utc) - timedelta(days=18)).isoformat(),
    },
    {
        "store": "apple_app_store",
        "review_id": "sample-as-002",
        "rating": 1,
        "title": "Sync issues",
        "review_text": "Broker connection keeps failing. Support helped but issue returned after a week.",
        "review_date": (datetime.now(timezone.utc) - timedelta(days=40)).isoformat(),
    },
    {
        "store": "google_play",
        "review_id": "sample-gp-003",
        "rating": 3,
        "title": "Decent",
        "review_text": "Works for basic monitoring. Would like better export for tax reporting.",
        "review_date": (datetime.now(timezone.utc) - timedelta(days=55)).isoformat(),
    },
    {
        "store": "apple_app_store",
        "review_id": "sample-as-003",
        "rating": 5,
        "title": "Finally all accounts in one place",
        "review_text": "Portfolio sync across banks is reliable now. Onboarding tutorial was helpful.",
        "review_date": (datetime.now(timezone.utc) - timedelta(days=8)).isoformat(),
    },
    {
        "store": "google_play",
        "review_id": "sample-gp-004",
        "rating": 2,
        "title": "Slow loads",
        "review_text": "Charts take forever on older Android. Crashes when switching to transactions tab.",
        "review_date": (datetime.now(timezone.utc) - timedelta(days=33)).isoformat(),
    },
    {
        "store": "apple_app_store",
        "review_id": "sample-as-004",
        "rating": 4,
        "title": "Solid app",
        "review_text": "UI refresh looks modern. Still waiting for custom notification schedules.",
        "review_date": (datetime.now(timezone.utc) - timedelta(days=15)).isoformat(),
    },
]


def load_sample_reviews() -> pd.DataFrame:
    df = pd.DataFrame(SAMPLE_REVIEWS)
    df["is_sample"] = True
    return df
