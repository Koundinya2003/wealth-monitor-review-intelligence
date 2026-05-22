# App package

See the [project README](../README.md) for full setup, architecture, and commands.

Quick start:

```bash
cd app
python3 -m venv .venv && source .venv/bin/activate
pip install app-store-scraper google-play-scraper
pip install -r requirements.txt
cp .env.example .env
python -m src.run_pipeline --sample
streamlit run src/dashboard.py
```
