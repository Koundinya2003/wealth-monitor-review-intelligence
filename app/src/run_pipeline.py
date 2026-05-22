"""End-to-end weekly pipeline orchestration."""

from __future__ import annotations

import argparse

from src import config
from src.fetch_reviews import fetch_all_reviews
from src.generate_email import generate_email_draft
from src.generate_report import generate_weekly_pulse
from src.logging_config import setup_logging
from src.theme_analysis import analyze_themes
from src.visualizations import build_sentiment_chart

logger = setup_logging()


def run_pipeline(
    skip_fetch: bool = False,
    use_sample: bool | None = None,
) -> None:
    config.ensure_dirs()

    if not skip_fetch:
        fetch_all_reviews(use_sample=use_sample)
    else:
        logger.info("Skipping fetch; using existing %s", config.REVIEWS_CSV)

    analysis = analyze_themes()
    themed_df = analysis["themed_reviews"]
    build_sentiment_chart(themed_df)
    generate_weekly_pulse(
        {k: v for k, v in analysis.items() if k != "themed_reviews"}
    )
    generate_email_draft(
        {k: v for k, v in analysis.items() if k != "themed_reviews"}
    )
    logger.info("Pipeline complete.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Wealth Monitor review intelligence pipeline")
    parser.add_argument("--skip-fetch", action="store_true", help="Use existing reviews.csv")
    parser.add_argument(
        "--sample",
        action="store_true",
        help="Force DEMO/SAMPLE review data",
    )
    args = parser.parse_args()
    run_pipeline(skip_fetch=args.skip_fetch, use_sample=True if args.sample else None)


if __name__ == "__main__":
    main()
