"""Import public App Store and Google Play reviews."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pandas as pd
from google_play_scraper import Sort, reviews as gp_reviews
from app_store_scraper import AppStore

from src import config
from src.clean_reviews import clean_reviews_df
from src.logging_config import setup_logging
from src.sample_data import load_sample_reviews

logger = setup_logging()

COLUMNS = ["store", "review_id", "rating", "title", "review_text", "review_date"]


def _cutoff_date() -> datetime:
    weeks = config.weeks_lookback()
    return datetime.now(timezone.utc) - timedelta(weeks=weeks)


def fetch_google_play(app_id: str, country: str = "us") -> pd.DataFrame:
    """Fetch public Google Play reviews via google-play-scraper."""
    logger.info("Fetching Google Play reviews for %s", app_id)
    cutoff = _cutoff_date()
    rows: list[dict] = []
    token = None

    while True:
        batch, token = gp_reviews(
            app_id,
            lang="en",
            country=country,
            sort=Sort.NEWEST,
            count=200,
            continuation_token=token,
        )
        if not batch:
            break
        for r in batch:
            at = r.get("at")
            if at is None:
                continue
            if at.tzinfo is None:
                at = at.replace(tzinfo=timezone.utc)
            if at < cutoff:
                token = None
                break
            rows.append(
                {
                    "store": "google_play",
                    "review_id": str(r.get("reviewId") or ""),
                    "rating": r.get("score"),
                    "title": "",
                    "review_text": r.get("content") or "",
                    "review_date": at.isoformat(),
                }
            )
        if token is None:
            break

    logger.info("Google Play: collected %d reviews in window", len(rows))
    return pd.DataFrame(rows, columns=COLUMNS) if rows else pd.DataFrame(columns=COLUMNS)


def fetch_apple_app_store(app_name: str, app_id: str, country: str) -> pd.DataFrame:
    """Fetch public Apple App Store reviews via app-store-scraper."""
    logger.info("Fetching App Store reviews for %s (%s)", app_name, app_id)
    cutoff = _cutoff_date()
    store = AppStore(country=country, app_name=app_name, app_id=app_id)
    store.review(how_many=500)

    rows: list[dict] = []
    for r in store.reviews:
        raw_date = r.get("date")
        if raw_date is None:
            continue
        if isinstance(raw_date, str):
            at = pd.to_datetime(raw_date, utc=True).to_pydatetime()
        else:
            at = raw_date
            if at.tzinfo is None:
                at = at.replace(tzinfo=timezone.utc)
        if at < cutoff:
            continue
        rows.append(
            {
                "store": "apple_app_store",
                "review_id": str(r.get("reviewId") or hash(str(r))),
                "rating": r.get("rating"),
                "title": r.get("title") or "",
                "review_text": r.get("review") or "",
                "review_date": at.isoformat(),
            }
        )

    logger.info("App Store: collected %d reviews in window", len(rows))
    return pd.DataFrame(rows, columns=COLUMNS) if rows else pd.DataFrame(columns=COLUMNS)


def fetch_all_reviews(use_sample: bool | None = None) -> pd.DataFrame:
    """Fetch from both stores, clean, and persist to CSV."""
    config.ensure_dirs()
    use_sample = config.use_sample_data() if use_sample is None else use_sample

    gp_id = config.google_play_app_id()
    apple_id = config.apple_app_id()
    if use_sample or (not gp_id and not apple_id):
        logger.warning("Using DEMO/SAMPLE review data (not live store data).")
        df = load_sample_reviews()
        if "is_sample" in df.columns:
            df = df.drop(columns=["is_sample"])
    else:
        frames: list[pd.DataFrame] = []
        if gp_id:
            try:
                frames.append(fetch_google_play(gp_id))
            except Exception as exc:
                logger.error("Google Play fetch failed: %s", exc)
        else:
            logger.warning("GOOGLE_PLAY_APP_ID not set; skipping Google Play.")

        if apple_id:
            try:
                frames.append(
                    fetch_apple_app_store(
                        config.app_name(),
                        apple_id,
                        config.apple_country(),
                    )
                )
            except Exception as exc:
                logger.error("App Store fetch failed: %s", exc)
        else:
            logger.warning("APPLE_APP_ID not set; skipping App Store.")

        if not frames:
            logger.warning("No store data fetched; falling back to SAMPLE data.")
            df = load_sample_reviews().drop(columns=["is_sample"], errors="ignore")
        else:
            df = pd.concat(frames, ignore_index=True)

    cleaned = clean_reviews_df(df)
    cleaned.to_csv(config.REVIEWS_CSV, index=False)
    logger.info("Saved %d reviews to %s", len(cleaned), config.REVIEWS_CSV)
    return cleaned


if __name__ == "__main__":
    fetch_all_reviews()
