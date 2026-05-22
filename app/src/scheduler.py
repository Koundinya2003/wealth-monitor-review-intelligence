"""Optional weekly automation — run pipeline on a schedule (local cron alternative)."""

from __future__ import annotations

import argparse
import time
from datetime import datetime

from src.logging_config import setup_logging
from src.run_pipeline import run_pipeline

logger = setup_logging()


def run_once() -> None:
    logger.info("Scheduled run started at %s", datetime.utcnow().isoformat())
    run_pipeline()
    logger.info("Scheduled run finished.")


def run_loop(interval_hours: float = 168.0) -> None:
    """Default: 168 hours = weekly."""
    while True:
        run_once()
        sleep_seconds = interval_hours * 3600
        logger.info("Sleeping %.1f hours until next run.", interval_hours)
        time.sleep(sleep_seconds)


def main() -> None:
    parser = argparse.ArgumentParser(description="Weekly pipeline scheduler")
    parser.add_argument("--once", action="store_true", help="Run once and exit")
    parser.add_argument(
        "--interval-hours",
        type=float,
        default=168.0,
        help="Hours between runs (default 168 = weekly)",
    )
    args = parser.parse_args()
    if args.once:
        run_once()
    else:
        run_loop(args.interval_hours)


if __name__ == "__main__":
    main()
