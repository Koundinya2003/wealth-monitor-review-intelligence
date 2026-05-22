"""Sentiment and theme charts for reports and dashboard."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from src import config
from src.logging_config import setup_logging

logger = setup_logging()


def build_sentiment_chart(themed_df: pd.DataFrame, out_path: Path | None = None) -> Path:
    out = out_path or config.SENTIMENT_CHART
    config.ensure_dirs()

    fig, axes = plt.subplots(1, 2, figsize=(10, 4))

    sentiment_counts = themed_df["sentiment"].value_counts()
    colors = {"positive": "#2ecc71", "neutral": "#95a5a6", "negative": "#e74c3c"}
    labels = list(sentiment_counts.index)
    vals = [sentiment_counts.get(l, 0) for l in labels]
    bar_colors = [colors.get(l, "#3498db") for l in labels]

    axes[0].bar(labels, vals, color=bar_colors)
    axes[0].set_title("Sentiment Distribution")
    axes[0].set_ylabel("Reviews")

    theme_counts = themed_df["theme"].value_counts().head(5)
    axes[1].barh(theme_counts.index[::-1], theme_counts.values[::-1], color="#3498db")
    axes[1].set_title("Top Themes (max 5)")
    axes[1].set_xlabel("Reviews")

    plt.tight_layout()
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    logger.info("Saved sentiment chart to %s", out)
    return out


def load_analysis() -> dict:
    if not config.ANALYSIS_JSON.exists():
        raise FileNotFoundError("Run theme analysis first (analysis.json missing).")
    return json.loads(config.ANALYSIS_JSON.read_text(encoding="utf-8"))
