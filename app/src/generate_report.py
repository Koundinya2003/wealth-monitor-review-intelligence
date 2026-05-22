"""Weekly pulse report — Markdown and PDF."""

from __future__ import annotations

import json
from datetime import datetime, timezone

from fpdf import FPDF

from src import config
from src.logging_config import setup_logging
from src.prompts import load_prompt
from src.llm import chat_json

logger = setup_logging()

MAX_WORDS = 250


def _word_count(text: str) -> int:
    return len(text.split())


def _build_markdown_from_analysis(analysis: dict) -> str:
    stats = analysis["stats"]
    total = stats["total_reviews"]
    avg = stats["average_rating"]
    sp = stats["sentiment_pct"]
    pos_pct = sp.get("positive", 0)
    neg_pct = sp.get("negative", 0)

    lines = [
        "# Weekly Wealth Monitor Review Pulse",
        "",
        f"*Generated {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}*",
        "",
        "## Review Summary",
        f"- **Total reviews analyzed:** {total}",
        f"- **Average rating:** {avg:.2f} / 5",
        f"- **Positive vs negative:** {pos_pct}% positive · {neg_pct}% negative · {sp.get('neutral', 0)}% neutral",
        "",
        "## Top Themes",
    ]

    for theme in stats.get("top_themes", [])[:3]:
        lines.append(
            f"- **{theme['name']}** — {theme['pct']}% — {theme.get('explanation', 'Key customer topic this week.')}"
        )

    lines.extend(["", "## Real User Quotes"])
    for q in analysis.get("quotes", [])[:3]:
        text = q.get("text", "").strip()
        if text:
            lines.append(f'- "{text}"')

    lines.extend(["", "## Recommended Actions"])
    for i, action in enumerate(analysis.get("actions", [])[:3], 1):
        lines.append(f"{i}. {action}")

    body = "\n".join(lines)
    if _word_count(body) > MAX_WORDS:
        logger.warning("Report exceeds %d words (%d); truncating quotes.", MAX_WORDS, _word_count(body))
        short_lines = lines[: lines.index("## Real User Quotes") + 1]
        for q in analysis.get("quotes", [])[:2]:
            short_lines.append(f'- "{q.get("text", "")[:80]}"')
        short_lines.extend(lines[lines.index("## Recommended Actions") :])
        body = "\n".join(short_lines)
    return body


def refine_executive_summary(analysis: dict) -> dict:
    """Optional LLM pass to tighten executive copy under word limit."""
    prompt = load_prompt(
        "executive_summary",
        app_name=config.app_name(),
        max_words=str(MAX_WORDS),
        analysis_json=json.dumps(
            {
                "stats": analysis["stats"],
                "quotes": analysis.get("quotes", []),
                "actions": analysis.get("actions", []),
            },
            ensure_ascii=False,
        ),
    )
    try:
        refined = chat_json(prompt)
        if refined.get("top_themes"):
            analysis["stats"]["top_themes"] = refined["top_themes"][:3]
        if refined.get("quotes"):
            analysis["quotes"] = refined["quotes"][:3]
        if refined.get("actions"):
            analysis["actions"] = refined["actions"][:3]
    except Exception as exc:
        logger.warning("Executive summary refinement skipped: %s", exc)
    return analysis


def write_markdown(content: str, path=None) -> str:
    out = path or config.WEEKLY_PULSE_MD
    config.ensure_dirs()
    out.write_text(content, encoding="utf-8")
    logger.info("Wrote markdown report to %s", out)
    return str(out)


def _pdf_safe(text: str) -> str:
    """FPDF core fonts are Latin-1; normalize common Unicode punctuation."""
    replacements = {
        "\u2014": "-",
        "\u2013": "-",
        "\u00b7": "|",
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
    }
    for src, dst in replacements.items():
        text = text.replace(src, dst)
    return text.encode("latin-1", errors="replace").decode("latin-1")


def write_pdf_from_markdown(md_content: str, path=None) -> str:
    out = path or config.WEEKLY_PULSE_PDF
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_margins(15, 15, 15)
    pdf.add_page()
    pdf.set_font("Helvetica", size=11)
    width = pdf.epw

    for line in md_content.splitlines():
        clean = _pdf_safe(line.strip())
        if not clean:
            pdf.ln(4)
            continue
        if clean.startswith("# "):
            pdf.set_font("Helvetica", "B", 16)
            pdf.multi_cell(width, 8, clean[2:])
            pdf.set_font("Helvetica", size=11)
        elif clean.startswith("## "):
            pdf.set_font("Helvetica", "B", 13)
            pdf.multi_cell(width, 7, clean[3:])
            pdf.set_font("Helvetica", size=11)
        elif clean.startswith("*"):
            pdf.set_font("Helvetica", "I", 10)
            pdf.multi_cell(width, 5, clean.strip("*"))
            pdf.set_font("Helvetica", size=11)
        else:
            pdf.multi_cell(width, 5, clean)

    pdf.output(str(out))
    logger.info("Wrote PDF report to %s", out)
    return str(out)


def generate_weekly_pulse(analysis: dict | None = None) -> tuple[str, str]:
    config.ensure_dirs()
    if analysis is None:
        analysis = json.loads(config.ANALYSIS_JSON.read_text(encoding="utf-8"))

    analysis = refine_executive_summary(analysis)
    md = _build_markdown_from_analysis(analysis)
    write_markdown(md)
    write_pdf_from_markdown(md)
    return str(config.WEEKLY_PULSE_MD), str(config.WEEKLY_PULSE_PDF)


if __name__ == "__main__":
    generate_weekly_pulse()
