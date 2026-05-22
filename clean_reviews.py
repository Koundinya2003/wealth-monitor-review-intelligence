"""Review cleaning, deduplication, and normalization."""

from __future__ import annotations

import hashlib
import re
import unicodedata
from typing import Iterable

import pandas as pd

from src.logging_config import setup_logging

logger = setup_logging()

REQUIRED_COLUMNS = ["store", "review_id", "rating", "title", "review_text", "review_date"]


def _normalize_text(text: str) -> str:
    if not isinstance(text, str):
        return ""
    text = unicodedata.normalize("NFKC", text)
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _review_fingerprint(row: pd.Series) -> str:
    key = "|".join(
        [
            str(row.get("store", "")),
            str(row.get("review_id", "")),
            str(row.get("review_date", ""))[:10],
            str(row.get("rating", "")),
            _normalize_text(str(row.get("review_text", "")))[:200],
        ]
    )
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def clean_reviews_df(df: pd.DataFrame) -> pd.DataFrame:
    """Deduplicate, strip malformed text, and drop empty reviews."""
    if df.empty:
        logger.warning("No reviews to clean.")
        return df

    working = df.copy()
    for col in REQUIRED_COLUMNS:
        if col not in working.columns:
            working[col] = ""

    working["title"] = working["title"].astype(str).map(_normalize_text)
    working["review_text"] = working["review_text"].astype(str).map(_normalize_text)
    working["rating"] = pd.to_numeric(working["rating"], errors="coerce")
    working["review_date"] = pd.to_datetime(working["review_date"], errors="coerce", utc=True)

    before = len(working)
    working = working.dropna(subset=["review_date", "rating"])
    working = working[
        (working["review_text"].str.len() > 0)
        | (working["title"].str.len() > 0)
    ]
    working["review_text"] = working.apply(
        lambda r: r["review_text"] if r["review_text"] else r["title"],
        axis=1,
    )
    working = working[working["review_text"].str.len() > 0]

    working["_fp"] = working.apply(_review_fingerprint, axis=1)
    working = working.drop_duplicates(subset=["_fp"], keep="first").drop(columns=["_fp"])
    working = working.sort_values("review_date", ascending=False).reset_index(drop=True)

    logger.info("Cleaned reviews: %d -> %d", before, len(working))
    return working[REQUIRED_COLUMNS]


def clean_reviews_file(path: str | None = None) -> pd.DataFrame:
    from src.config import REVIEWS_CSV

    csv_path = path or str(REVIEWS_CSV)
    df = pd.read_csv(csv_path)
    cleaned = clean_reviews_df(df)
    cleaned.to_csv(csv_path, index=False)
    return cleaned


def rows_for_analysis(df: pd.DataFrame, max_rows: int = 120) -> list[dict]:
    """Compact payloads for LLM (no PII fields)."""
    subset = df.head(max_rows)
    records: list[dict] = []
    for idx, (_, row) in enumerate(subset.iterrows()):
        records.append(
            {
                "review_index": idx,
                "rating": float(row["rating"]),
                "title": str(row.get("title", ""))[:120],
                "review_text": str(row.get("review_text", ""))[:500],
                "review_date": str(row.get("review_date", ""))[:10],
            }
        )
    return records
