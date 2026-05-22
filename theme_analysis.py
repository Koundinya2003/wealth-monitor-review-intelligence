"""AI-powered theme clustering and sentiment assignment."""

from __future__ import annotations

import json
from typing import Any

import pandas as pd

from src import config
from src.clean_reviews import rows_for_analysis
from src.llm import chat_json
from src.logging_config import setup_logging
from src.prompts import load_prompt

logger = setup_logging()

MAX_THEMES = 5


def _merge_theme_results(df: pd.DataFrame, theme_payload: dict[str, Any]) -> pd.DataFrame:
    themed = df.copy().reset_index(drop=True)
    themed["theme"] = "General"
    themed["sentiment"] = "neutral"

    assignments = theme_payload.get("reviews", [])
    for item in assignments:
        idx = int(item.get("review_index", -1))
        if 0 <= idx < len(themed):
            themed.loc[idx, "theme"] = str(item.get("theme", "General"))[:80]
            sentiment = str(item.get("sentiment", "neutral")).lower()
            if sentiment not in {"positive", "neutral", "negative"}:
                sentiment = "neutral"
            themed.loc[idx, "sentiment"] = sentiment

    return themed


def _compute_stats(themed: pd.DataFrame) -> dict[str, Any]:
    total = len(themed)
    avg_rating = float(themed["rating"].mean()) if total else 0.0
    sentiment_counts = themed["sentiment"].value_counts().to_dict()
    positive = sentiment_counts.get("positive", 0)
    negative = sentiment_counts.get("negative", 0)
    neutral = sentiment_counts.get("neutral", 0)

    theme_counts = themed["theme"].value_counts()
    top_themes = []
    for name, count in theme_counts.head(3).items():
        pct = round(100 * count / total, 1) if total else 0
        top_themes.append({"name": name, "pct": pct, "count": int(count)})

    return {
        "total_reviews": total,
        "average_rating": round(avg_rating, 2),
        "sentiment_counts": {
            "positive": int(positive),
            "negative": int(negative),
            "neutral": int(neutral),
        },
        "sentiment_pct": {
            "positive": round(100 * positive / total, 1) if total else 0,
            "negative": round(100 * negative / total, 1) if total else 0,
            "neutral": round(100 * neutral / total, 1) if total else 0,
        },
        "top_themes": top_themes,
        "theme_breakdown": [
            {"name": k, "pct": round(100 * v / total, 1) if total else 0, "count": int(v)}
            for k, v in theme_counts.items()
        ],
    }


def analyze_themes(df: pd.DataFrame | None = None) -> dict[str, Any]:
    """Run full AI analysis pipeline and persist JSON results."""
    config.ensure_dirs()
    if df is None:
        df = pd.read_csv(config.REVIEWS_CSV)
    if df.empty:
        raise ValueError("No reviews available for analysis.")

    records = rows_for_analysis(df.reset_index(drop=True))
    clustering_prompt = load_prompt(
        "theme_clustering",
        app_name=config.app_name(),
        weeks=str(config.weeks_lookback()),
        max_themes=str(MAX_THEMES),
        reviews_json=json.dumps(records, ensure_ascii=False),
    )
    logger.info("Running theme clustering (%d reviews)...", len(records))
    theme_payload = chat_json(clustering_prompt)
    themed_df = _merge_theme_results(df.reset_index(drop=True), theme_payload)

    stats = _compute_stats(themed_df)
    theme_descriptions = {
        t.get("name", ""): t.get("description", "")
        for t in theme_payload.get("themes", [])
    }
    for item in stats["top_themes"]:
        item["explanation"] = theme_descriptions.get(item["name"], "Frequently mentioned in recent reviews.")

    reviews_sample = themed_df[["rating", "theme", "sentiment", "review_text"]].head(40).to_dict(
        orient="records"
    )
    quotes_prompt = load_prompt(
        "quote_extraction",
        app_name=config.app_name(),
        reviews_sample=json.dumps(reviews_sample, ensure_ascii=False),
    )
    logger.info("Extracting representative quotes...")
    quotes_payload = chat_json(quotes_prompt)

    context = {**stats, "themes": theme_payload.get("themes", []), "quotes": quotes_payload.get("quotes", [])}
    actions_prompt = load_prompt(
        "action_recommendations",
        app_name=config.app_name(),
        context_json=json.dumps(context, ensure_ascii=False),
    )
    logger.info("Generating action recommendations...")
    actions_payload = chat_json(actions_prompt)

    analysis = {
        "app_name": config.app_name(),
        "weeks_lookback": config.weeks_lookback(),
        "stats": stats,
        "themes_meta": theme_payload.get("themes", []),
        "quotes": quotes_payload.get("quotes", [])[:3],
        "actions": (actions_payload.get("actions") or [])[:3],
        "themed_reviews": themed_df,
    }

    serializable = {
        k: v for k, v in analysis.items() if k != "themed_reviews"
    }
    config.ANALYSIS_JSON.write_text(
        json.dumps(serializable, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    themed_df.to_csv(config.DATA_DIR / "reviews_analyzed.csv", index=False)
    logger.info("Analysis saved to %s", config.ANALYSIS_JSON)
    return analysis


if __name__ == "__main__":
    analyze_themes()
