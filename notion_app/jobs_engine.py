"""
jobs_engine.py — pulls jobs from Adzuna API, bank career page scrapers,
and static high-priority source links.
"""

import requests
from bs4 import BeautifulSoup

ADZUNA_APP_ID  = "bf6e24e0"
ADZUNA_API_KEY = "68aeb5a0a35122991e14a00956425df9"
ADZUNA_BASE    = "https://api.adzuna.com/v1/api/jobs/us/search/1"

TARGET_LOCATIONS = ["Houston, TX", "Cypress, TX", "Spring, TX", "The Woodlands, TX", "Tomball, TX"]

SEARCH_QUERIES = [
    "bank teller",
    "personal banker",
    "business analyst",
    "operations analyst",
    "data analyst",
]


# ── Adzuna ────────────────────────────────────────────────────────────────────

def search_adzuna() -> list[dict]:
    jobs = []
    seen = set()

    for query in SEARCH_QUERIES:
        for location in TARGET_LOCATIONS:
            try:
                params = {
                    "app_id":          ADZUNA_APP_ID,
                    "app_key":         ADZUNA_API_KEY,
                    "results_per_page": 10,
                    "what":            query,
                    "where":           location,
                    "distance":        25,
                    "sort_by":         "date",
                }
                r = requests.get(ADZUNA_BASE, params=params, timeout=10)
                r.raise_for_status()
                results = r.json().get("results", [])

                for item in results:
                    link = item.get("redirect_url", "")
                    if not link or link in seen:
                        continue
                    seen.add(link)

                    loc = item.get("location", {})
                    area = loc.get("area", [])
                    city = area[-1] if area else location

                    jobs.append({
                        "company":  (item.get("company") or {}).get("display_name", "—"),
                        "title":    item.get("title", "—"),
                        "location": city,
                        "link":     link,
                    })
            except Exception:
                continue

    return jobs


# ── Bank Career Page Scrapers ─────────────────────────────────────────────────

def _scrape_woodforest() -> list[dict]:
    """Woodforest National Bank — Taleo career portal."""
    jobs = []
    keywords = ["teller", "banker", "associate", "relationship"]
    try:
        url = "https://woodforest.taleo.net/careersection/2/jobsearch.ftl?lang=en"
        r = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(r.text, "html.parser")
        for link in soup.find_all("a"):
            title = link.get_text().strip()
            if not title or not any(kw in title.lower() for kw in keywords):
                continue
            href = link.get("href", "")
            if href and not href.startswith("http"):
                href = "https://woodforest.taleo.net" + href
            if href:
                jobs.append({
                    "company":  "Woodforest National Bank",
                    "title":    title,
                    "location": "Houston Area, TX",
                    "link":     href,
                })
    except Exception:
        pass
    return jobs


def search_bank_sites() -> list[dict]:
    """Run all bank career page scrapers and combine results."""
    jobs = []
    jobs += _scrape_woodforest()
    return jobs


# ── Static High-Priority Sources ──────────────────────────────────────────────

def static_sources() -> list[dict]:
    """Direct links to bank career portals. Always included."""
    return [
        {
            "company":  "First Convenience Bank (FNBT)",
            "title":    "Teller / Banker — View Open Roles",
            "location": "Houston Area, TX",
            "link":     "https://myjobs.adp.com/fnbtandfcbcareers/cx",
        },
        {
            "company":  "Prosperity Bank",
            "title":    "Retail Banking — View Open Roles",
            "location": "Texas",
            "link":     "https://www.prosperitybankusa.com/Careers",
        },
        {
            "company":  "PNC Bank",
            "title":    "Regional Banker / Teller — View Open Roles",
            "location": "Houston Area, TX",
            "link":     "https://careers.pnc.com",
        },
        {
            "company":  "Bank of America",
            "title":    "Financial Center Roles — View Open Roles",
            "location": "Houston Area, TX",
            "link":     "https://careers.bankofamerica.com",
        },
        {
            "company":  "Wells Fargo",
            "title":    "Banking Roles — View Open Roles",
            "location": "Houston Area, TX",
            "link":     "https://www.wellsfargojobs.com",
        },
        {
            "company":  "JPMorgan Chase",
            "title":    "Branch Banking — View Open Roles",
            "location": "Houston Area, TX",
            "link":     "https://jpmc.fa.oraclecloud.com",
        },
        {
            "company":  "Woodforest National Bank",
            "title":    "Branch Banking Roles — View Open Roles",
            "location": "Houston Area, TX",
            "link":     "https://woodforest.taleo.net",
        },
    ]


# ── Main Engine ───────────────────────────────────────────────────────────────

def get_all_jobs() -> list[dict]:
    """Combine all sources and deduplicate by link."""
    jobs = []
    jobs += search_adzuna()
    jobs += search_bank_sites()
    jobs += static_sources()

    # Deduplicate by link
    seen = set()
    unique = []
    for job in jobs:
        if job["link"] not in seen:
            seen.add(job["link"])
            unique.append(job)

    return unique
