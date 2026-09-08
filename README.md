# Ellis

A Python job search tool built to find and track banking/analytics roles in the Houston area. Combines a scoring/analysis CLI with Claude API integration and a Flask web dashboard for tracking applications day to day.

## What it does

- **Pulls live job listings** from the Adzuna API, direct bank career-page scraping (BeautifulSoup), and a curated list of target employers (Woodforest, Prosperity Bank, PNC, Bank of America, Wells Fargo, JPMorgan Chase, and others).
- **Scores and analyzes role fit** — the CLI (`app.py`) filters listings by target location and role keywords, scores each one, and uses the Claude API (`claude-haiku-4-5`) to generate a short analysis of why a specific role is or isn't a strong fit, and what to lead with.
- **Tracks applications** through a Notion-style Flask web dashboard (`notion_app/`) — save jobs from search results, move them through statuses (Not Applied → Applied → Interview → Offer/Rejected), and keep notes per application.

## Project structure

- **`app.py`** — the CLI: filtering, scoring, and Claude-based fit analysis
- **`notion_app/`** — the Flask web dashboard (the actively used, day-to-day tool)
- **`talentscope/`** — a FastAPI-based extension (candidate profile, scheduled daily scans, fit-score alerts) — in progress, not covered in the setup below

## Setup (notion_app — the Flask dashboard)

```bash
git clone https://github.com/fridaperalta11-a11y/ellis-job-search.git
cd ellis-job-search/notion_app
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file in `notion_app/` (this is gitignored — never commit it) with your own Adzuna API credentials, free to register at [developer.adzuna.com](https://developer.adzuna.com/):
```
ADZUNA_APP_ID=your_app_id
ADZUNA_API_KEY=your_api_key
```

Run it:
```bash
python3 app.py
```
Open `http://127.0.0.1:5001`.

## Setup (CLI + Claude analysis)

```bash
cd ellis-job-search
pip install anthropic requests beautifulsoup4
export ANTHROPIC_API_KEY=your_key
python3 app.py
```

## Tech stack

- Python
- Flask — the web dashboard
- Adzuna API + BeautifulSoup — live job data
- Anthropic Claude API — role-fit analysis
- FastAPI + SQLAlchemy — `talentscope/` (in progress)

