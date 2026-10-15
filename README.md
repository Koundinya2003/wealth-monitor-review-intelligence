<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/readme/01_hero_dark.svg">
  <img src="docs/readme/01_hero_light.svg" width="100%" alt="Wealth Coach AI, a personal finance coach. Every paycheck, a plan. It tells first time investors where this month's money should go, and why. For everyday Indians earning ₹20,000 to ₹5,00,000 a month: enter salary, expenses, age, goal and risk appetite, and get a plan, ranked opportunities and a growth path. The question it answers: given my income, where should I invest my money this month? Chart: SIP growth for the default profile at the 12% a year the app assumes, reaching ₹36.8L after 10 years at ₹16,000 a month. Projection math from the app's wealth journey chart; illustrative, not a promise of returns.">
</picture>

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/readme/02_planner_dark.svg">
  <img src="docs/readme/02_planner_light.svg" width="100%" alt="The planner: where the salary goes. Five inputs, a few plain rules, shown with the app's own default profile: salary ₹50,000, expenses ₹30,000, age 25, one of five goals, medium risk. Expenses take ₹30,000 (60% of salary), ₹16,000 is invested (80% of the ₹20,000 left over) and ₹4,000 is kept. Outputs: ₹20,000 available to invest (salary minus expenses), 40% savings rate (available divided by salary), ₹1,80,000 emergency fund target (6 times monthly expenses), ₹16,000 suggested each month (60, 80 or 90% of the surplus for low, medium or high risk). Investment readiness score 73 out of 100: savings rate 40 of 40 (30% or more earns the full 40), emergency fund progress 3 of 30 (one month's savings against the target), investment capacity 30 of 30 (investing 80% or more of surplus).">
</picture>

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/readme/03_discovery_dark.svg">
  <img src="docs/readme/03_discovery_light.svg" width="100%" alt="Discovery: market chatter in, ranked ideas out. Sources: RSS feeds from RBI, SEBI, Economic Times Markets, Business Standard Markets and Mint Markets; NewsAPI financial news by topic (optional key); Reddit r/IndiaInvestments, r/personalfinanceindia and r/IndianStreetBets; and a curated fallback of 22 demo articles when live sources are down. Stage 1, collect: up to 50 articles per source, 10 second timeout, 3 retries, duplicates removed. Stage 2, clean and classify: HTML stripped, 50 to 10,000 characters kept, tagged as investment, savings, retirement, tax, insurance, real estate, crypto or market trends. Stage 3, analyze with an LLM: OpenRouter, DeepSeek V3 by default, returns structured JSON with top opportunities, market summary, policy updates, recommendations and risks. Stage 4, personalize: each opportunity is scored 0 to 100 against your profile.">
</picture>

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/readme/04_ranking_dark.svg">
  <img src="docs/readme/04_ranking_light.svg" width="100%" alt="Personal ranking: 100 points of fit. Six parts: risk alignment 25, goal alignment 25, affordability 20, age 15, savings rate 10, AI confidence 5. An exact risk match earns the full 25; goals map to keywords, such as retirement to PPF, NPS and pension, and wealth creation to index, equity, mutual funds and SIP. Under 30 leans to growth, under 40 to balance, under 55 to stability, then to capital preservation. High savers can take more market risk; very low savers are steered to an emergency fund first. Stars: 80 and above highly recommended (five stars), 60 to 79 good fit (four), 40 to 59 moderate fit (three), below 40 not recommended (one).">
</picture>

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/readme/05_compare_dark.svg">
  <img src="docs/readme/05_compare_light.svg" width="100%" alt="Compare: eight instruments, one table, using reference values stored in the app (not live market data or guarantees). Index funds (Nifty 50): 10 to 14%, medium risk, high liquidity, no lock in. ELSS tax saver: 12 to 15%, medium risk, medium liquidity, 3 years. PPF: 7.1% fixed, low risk, low liquidity, 15 years. NPS: 9 to 12%, medium risk, very low liquidity, until age 60. Short term debt funds: 7 to 9%, low risk, high liquidity, none. Gold ETF or SGB: 8 to 12%, low risk, SGB 8 years. Emergency fund in a liquid fund: 4 to 6%, low risk, very high liquidity, none. Fixed deposits: 6 to 7.5%, low risk, medium liquidity, 1 to 5 years.">
</picture>

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/readme/06_stack_dark.svg">
  <img src="docs/readme/06_stack_light.svg" width="100%" alt="Stack and roadmap. Most finance apps track spending; this one is about growing what is left. Stack: Streamlit multipage interface, OpenRouter with DeepSeek V3 by default, Plotly allocation and growth charts, Pandas and NumPy for data processing, SQLite via SQLAlchemy for profiles and plans, feedparser and requests for RSS, NewsAPI and Reddit. Roadmap: live NSE and BSE data, real time fund NAV tracking, rebalancing suggestions, goal based planning, AI powered SIP optimization, tax planning assistant, brokerage integrations, stock and ETF screening, financial document parsing, mobile application. Not advice: an educational and portfolio project; recommendations generated by the application are not professional investment advice. Built by Aditya K. Koundinya.">
</picture>

# Wealth Coach AI

> An AI powered personal finance coach that helps everyday Indians understand, manage and grow their wealth through personalized investment planning and intelligent market insights.

**[Live demo](https://wealth-monitor-review-intelligence-9oixsvognm4vryrrlagbta.streamlit.app/)**

## Overview

Managing personal finances should not require a financial advisor or years of investing experience.

**Wealth Coach AI** is an AI first financial planning platform built for individuals earning anywhere from **₹20,000 to ₹5,00,000 per month**. Instead of overwhelming users with financial jargon, it analyzes their financial profile and provides personalized investment recommendations, wealth projections and market opportunities tailored to their goals. It combines traditional financial planning with AI powered investment discovery to make wealth creation simple, accessible and actionable.

The app itself lives in [`wealth-coach-ai/`](wealth-coach-ai), which has its own, more detailed [README](wealth-coach-ai/README.md).

## Features

### Personalized wealth dashboard

* Financial health score (investment readiness, out of 100)
* Monthly savings analysis
* Net worth tracking
* Expense insights
* Goal progress monitoring

### AI investment planner

Generates personalized investment allocations based on salary, monthly expenses, age, financial goals (emergency fund, buy house, travel, retirement, wealth creation) and risk appetite (low, medium, high).

Recommended allocations include index funds, mutual funds, debt funds, gold ETFs, an emergency fund and tax saving investments.

### AI investment discovery engine

Discovers investment opportunities from financial RSS feeds, market news (NewsAPI), Reddit investing communities and a curated fallback investment dataset.

The AI extracts investment opportunities, market trends, risk indicators, key insights and actionable recommendations.

### Investment comparison

Compare investments by expected returns, risk, liquidity, tax benefits, investment horizon, minimum investment and suitability.

### AI financial advisor

Generates personalized guidance: investment suggestions, wealth building strategies, risk management, portfolio recommendations and market summaries.

### Wealth growth simulator

Visualize how your investments grow over time. Simulate different monthly investment amounts and compare long term wealth outcomes.

## How it works

```text
User Profile
        │
        ▼
Financial Analysis
        │
        ▼
Investment Planning
        │
        ▼
Market Discovery
        │
        ▼
AI Opportunity Analysis
        │
        ▼
Personalized Recommendations
```

## Architecture

```
wealth-coach-ai/
├── app.py
├── pages/
│   ├── Dashboard
│   ├── Investment Discovery
│   ├── Investment Comparison
│   └── Wealth Planner
├── services/
│   ├── ai/
│   ├── discovery/
│   └── finance/
├── database/
├── config/
├── data/
└── assets/
```

## Tech stack

* **Frontend:** Streamlit
* **Backend:** Python
* **AI:** OpenRouter, DeepSeek V3
* **Data processing:** Pandas, NumPy
* **Charts:** Plotly
* **Data sources:** RSS feeds, NewsAPI, Reddit, curated investment dataset
* **Database:** SQLite (via SQLAlchemy)

## Installation

Clone the repository:

```bash
git clone https://github.com/Koundinya2003/wealth-monitor-review-intelligence.git
```

Move into the project:

```bash
cd wealth-monitor-review-intelligence/wealth-coach-ai
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create a `.env` file (or copy `.env.example`):

```env
OPENROUTER_API_KEY=your_api_key
OPENROUTER_MODEL=deepseek/deepseek-chat-v3-0324:free

NEWSAPI_API_KEY=your_key
```

Optional variables listed in `.env.example`: `OPENAI_API_KEY` (fallback if OpenRouter is unavailable), `DATABASE_URL` (SQLite file, default `wealth.db`), `REDDIT_API_KEY`, `REDDIT_API_SECRET` and `REDDIT_USER_AGENT`. Without live sources the discovery page falls back to a curated dataset.

Run the application:

```bash
streamlit run app.py
```

## Live demo

Try the application here: https://wealth-monitor-review-intelligence-9oixsvognm4vryrrlagbta.streamlit.app/

## Future improvements

* Live NSE and BSE market integration
* Real time mutual fund NAV tracking
* Portfolio rebalancing suggestions
* Goal based financial planning
* AI powered SIP optimization
* Tax planning assistant
* Brokerage integrations
* Stock and ETF screening
* Financial document parsing
* Mobile application

## Why this project?

Most personal finance applications focus on tracking expenses. **Wealth Coach AI** focuses on **growing wealth**.

The goal is to simplify investing for first time investors by combining personalized financial planning with AI driven investment discovery, making wealth management accessible to everyone regardless of their financial background.

## Rebuilding the panels

The images at the top are SVG panels generated from one HTML page. Edit `docs/readme/one_sheet.html`, then run:

```bash
node docs/readme/build_readme_svgs.js docs/readme/one_sheet.html docs/readme 960
```

This needs Node with Playwright installed, and curl (fonts are fetched from Google Fonts and embedded).

## Author

**Aditya K. Koundinya**

* GitHub: https://github.com/Koundinya2003
* LinkedIn: https://www.linkedin.com/in/adityakkoundinya/

## License

This project is intended for educational and portfolio purposes.

Financial recommendations generated by the application should not be considered professional investment advice.
