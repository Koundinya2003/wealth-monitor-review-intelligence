# Wealth Monitor · App Review Intelligence System

Production-style pipeline that imports public App Store and Google Play reviews, analyzes them with OpenAI, groups feedback into at most five themes, and produces a weekly executive pulse (Markdown + PDF) plus an email draft. Includes a Streamlit dashboard for Product, Growth, Support, and Leadership.

## Architecture

```text
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────────┐
│ fetch_reviews   │────▶│ clean_reviews    │────▶│ data/reviews.csv    │
│ (public APIs)   │     │ dedupe + normalize│     └──────────┬──────────┘
└─────────────────┘     └──────────────────┘                │
                                                                ▼
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────────┐
│ prompts/        │────▶│ theme_analysis   │────▶│ output/analysis.json │
│ reusable LLM    │     │ OpenAI GPT-4o    │     │ reviews_analyzed.csv │
└─────────────────┘     └──────────────────┘     └──────────┬──────────┘
                                                                │
                    ┌───────────────────────────────────────────┼───────────────────────────┐
                    ▼                                           ▼                           ▼
           generate_report.py                          generate_email.py          visualizations.py
           weekly_pulse.md / .pdf                      email_draft.md             sentiment_chart.png
                    │
                    ▼
           dashboard.py (Streamlit + Plotly)
```

## Project layout

```text
wealth-monitor-review-intelligence/
├── README.md
└── app/
    ├── .env.example
    ├── requirements.txt
    ├── README.md
    ├── data/
    │   └── reviews.csv          # generated
    ├── output/
    │   ├── weekly_pulse.md
    │   ├── weekly_pulse.pdf
    │   ├── email_draft.md
    │   ├── sentiment_chart.png
    │   └── analysis.json
    └── src/
        ├── fetch_reviews.py
        ├── clean_reviews.py
        ├── theme_analysis.py
        ├── generate_report.py
        ├── generate_email.py
        ├── dashboard.py
        ├── run_pipeline.py
        ├── scheduler.py
        ├── llm.py
        ├── sample_data.py
        └── prompts/
```

## Setup

### 1. Python environment

```bash
cd /Users/adityakkoundinya/Projects/wealth-monitor-review-intelligence/app
python3 -m venv .venv
source .venv/bin/activate
pip install app-store-scraper google-play-scraper
pip install -r requirements.txt
```

### 2. Environment variables

```bash
cp .env.example .env
```

Edit `.env`:

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | Required for AI analysis |
| `OPENAI_MODEL` | Default `gpt-4o` |
| `GOOGLE_PLAY_APP_ID` | Play package id (e.g. `com.wealthmonitor.app`) |
| `APPLE_APP_ID` | Numeric App Store id |
| `APPLE_COUNTRY` | Store country code (default `us`) |
| `WEEKS_LOOKBACK` | 8–12 weeks window (default `10`) |
| `USE_SAMPLE_DATA` | `true` for explicit **demo/sample** reviews |

### 3. App Store identifiers

Set real public app identifiers for **Wealth Monitor** in `.env`. Without them, the pipeline uses **labeled sample data** only (`sample_data.py`).

## How themes are generated

1. Reviews are batched (up to 120) and sent to OpenAI with `prompts/theme_clustering.txt`.
2. The model infers **at most 5 themes** and assigns each review a **theme** + **sentiment** (`positive` / `neutral` / `negative`).
3. `prompts/quote_extraction.txt` selects three short, PII-free quotes.
4. `prompts/action_recommendations.txt` proposes three product actions.
5. `generate_report.py` builds the executive Markdown/PDF (≤250 words) and may refine copy via `prompts/executive_summary.txt`.

No keyword matching — all grouping and narrative are LLM-driven.

## Example workflow

### Full weekly pipeline

```bash
cd app
source .venv/bin/activate
python -m src.run_pipeline
```

Demo mode (sample reviews, no store IDs):

```bash
python -m src.run_pipeline --sample
```

Skip fetch when `data/reviews.csv` already exists:

```bash
python -m src.run_pipeline --skip-fetch
```

### Individual steps

```bash
python -m src.fetch_reviews
python -m src.clean_reviews    # via CSV round-trip in fetch
python -m src.theme_analysis
python -m src.generate_report
python -m src.generate_email
```

### Streamlit dashboard

```bash
streamlit run src/dashboard.py
```

### Optional weekly scheduler

```bash
python -m src.scheduler --once
python -m src.scheduler --interval-hours 168
```

Cron example (Mondays 9:00):

```cron
0 9 * * 1 cd /path/to/app && .venv/bin/python -m src.run_pipeline >> logs/weekly.log 2>&1
```

## Outputs

| File | Description |
|------|-------------|
| `data/reviews.csv` | Cleaned, deduplicated reviews |
| `output/analysis.json` | Themes, stats, quotes, actions |
| `output/weekly_pulse.md` | Executive weekly report |
| `output/weekly_pulse.pdf` | PDF version |
| `output/email_draft.md` | Email draft (not sent) |
| `output/sentiment_chart.png` | Sentiment + theme chart |

## Constraints

- **Max 5 themes** enforced in prompts and charts
- **No PII** in prompts and outputs
- **No fake data** unless `USE_SAMPLE_DATA=true` or `--sample` (clearly marked sample)
- Reports target **≤250 words**, scannable sections

## Requirements

- Python 3.11+ (3.11 or 3.12 recommended; 3.13 works with two-step pip install below)
- Public store APIs only (`google-play-scraper`, `app-store-scraper`) — no authenticated scraping
- OpenAI API key for analysis

## Troubleshooting

- **`OPENAI_API_KEY is not set`** — add key to `app/.env`
- **Empty fetch** — verify app IDs; use `--sample` to validate the pipeline
- **App Store errors** — confirm `APPLE_APP_ID` and `APP_NAME` match the listing

## License

Internal / project use for Wealth Monitor product intelligence.
