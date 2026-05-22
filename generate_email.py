"""Professional email draft generator (no sending)."""

from __future__ import annotations

import json
from datetime import datetime, timezone

from src import config
from src.logging_config import setup_logging
from src.prompts import load_prompt
from src.llm import chat_json

logger = setup_logging()


def _fallback_email(analysis: dict) -> str:
    stats = analysis["stats"]
    themes = ", ".join(t["name"] for t in stats.get("top_themes", [])[:3])
    quotes = "\n".join(f'> "{q.get("text", "")}"' for q in analysis.get("quotes", [])[:3])
    actions = "\n".join(f"{i}. {a}" for i, a in enumerate(analysis.get("actions", [])[:3], 1))
    date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return f"""Subject: Weekly Wealth Monitor Review Pulse — {date}

Hi team,

Here is this week's App Review Intelligence pulse for Wealth Monitor.

**Highlights**
- Reviews analyzed: {stats.get("total_reviews", 0)}
- Average rating: {stats.get("average_rating", 0):.2f} / 5
- Top themes: {themes}

**User voice**
{quotes}

**Recommended actions**
{actions}

Best,
Product Ops
"""


def generate_email_draft(analysis: dict | None = None) -> str:
    config.ensure_dirs()
    if analysis is None:
        analysis = json.loads(config.ANALYSIS_JSON.read_text(encoding="utf-8"))

    pulse = {
        "stats": analysis["stats"],
        "quotes": analysis.get("quotes", []),
        "actions": analysis.get("actions", []),
    }
    prompt = load_prompt(
        "email_draft",
        app_name=config.app_name(),
        pulse_json=json.dumps(pulse, ensure_ascii=False),
    )

    try:
        payload = chat_json(prompt)
        subject = payload.get("subject", "Weekly Wealth Monitor Review Pulse")
        body = payload.get("body", "")
        content = f"# Email Draft\n\n**Subject:** {subject}\n\n---\n\n{body}\n"
    except Exception as exc:
        logger.warning("LLM email draft failed, using template: %s", exc)
        content = _fallback_email(analysis)

    config.EMAIL_DRAFT_MD.write_text(content, encoding="utf-8")
    logger.info("Wrote email draft to %s", config.EMAIL_DRAFT_MD)
    return content


if __name__ == "__main__":
    generate_email_draft()
