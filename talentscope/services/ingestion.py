"""
Ingestion service — fetches job postings from Adzuna and saves new ones to DB.
Deduplicates, geocodes, and scores each job before saving.
"""
import json
import logging
from datetime import date, datetime, timezone

import httpx

from config import ADZUNA_APP_ID, ADZUNA_API_KEY
from database import SessionLocal
from models import Job, CandidateProfile, ScanLog
from services.deduplication import make_fingerprint
from services.geocoding import geocode, haversine_miles
from services.scoring import calculate_fit_score

logger = logging.getLogger(__name__)

ADZUNA_BASE = "https://api.adzuna.com/v1/api/jobs/us/search"

# Target cities and their search terms
TARGET_LOCATIONS = [
    "Houston, TX",
    "Magnolia, TX",
    "Tomball, TX",
    "Spring, TX",
    "Cypress, TX",
    "The Woodlands, TX",
]

# Job keywords to search — two passes: analytical roles + banking roles
SEARCH_QUERIES = [
    "business analyst",
    "data analyst",
    "operations analyst",
    "research analyst",
    "program analyst",
    "systems analyst",
    "teller",
    "banker",
    "personal banker",
    "financial solutions advisor",
]


def _parse_date(date_str: str | None) -> date | None:
    if not date_str:
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d"):
        try:
            return datetime.strptime(date_str[:19], fmt).date()
        except ValueError:
            continue
    return None


def _parse_salary(item: dict) -> tuple[float | None, float | None, bool]:
    sal_min = item.get("salary_min")
    sal_max = item.get("salary_max")
    if sal_min or sal_max:
        return (
            float(sal_min) if sal_min else None,
            float(sal_max) if sal_max else None,
            True,
        )
    return None, None, False


def _parse_location(item: dict) -> tuple[str, str, str]:
    loc = item.get("location", {})
    display = loc.get("display_name", "")
    area = loc.get("area", [])
    city  = area[-1] if len(area) >= 1 else ""
    state = area[-2] if len(area) >= 2 else "TX"
    return city, state, display


async def _fetch_adzuna_page(
    query: str, location: str, page: int = 1, results_per_page: int = 20
) -> list[dict]:
    """Fetch one page of Adzuna results for a query + location."""
    if not ADZUNA_APP_ID or not ADZUNA_API_KEY:
        logger.warning("Adzuna API keys not configured — skipping")
        return []

    params = {
        "app_id": ADZUNA_APP_ID,
        "app_key": ADZUNA_API_KEY,
        "results_per_page": results_per_page,
        "what": query,
        "where": location,
        "distance": 30,          # miles radius around the location
        "sort_by": "date",       # most recent first
        "content-type": "application/json",
    }

    url = f"{ADZUNA_BASE}/{page}"
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(url, params=params)
            r.raise_for_status()
            data = r.json()
            return data.get("results", [])
    except httpx.HTTPStatusError as e:
        logger.error(f"Adzuna HTTP error {e.response.status_code} for '{query}' in {location}")
        return []
    except Exception as e:
        logger.error(f"Adzuna fetch failed: {e}")
        return []


async def run_scan() -> dict:
    """
    Full scan: fetch from Adzuna across all queries and locations,
    deduplicate, score, and save new jobs.
    Returns summary dict.
    """
    db = SessionLocal()
    scan_log = ScanLog(started_at=datetime.now(timezone.utc), sources_used='["adzuna"]')
    db.add(scan_log)
    db.commit()
    db.refresh(scan_log)

    jobs_fetched = 0
    jobs_new = 0
    jobs_deduped = 0

    try:
        # Get candidate home location for distance calc
        profile = db.query(CandidateProfile).filter(CandidateProfile.id == 1).first()
        home_lat, home_lng = None, None
        if profile and profile.location_lat and profile.location_lng:
            home_lat, home_lng = profile.location_lat, profile.location_lng
        # Skip geocoding home address during scan — done lazily on first access

        # Collect all raw results
        raw_items: list[dict] = []
        for query in SEARCH_QUERIES:
            for location in TARGET_LOCATIONS:
                items = await _fetch_adzuna_page(query, location, page=1, results_per_page=20)
                raw_items.extend(items)
                jobs_fetched += len(items)

        # Process each result
        seen_fingerprints: set[str] = set()

        for item in raw_items:
            company = (item.get("company", {}) or {}).get("display_name", "") or ""
            title   = item.get("title", "") or ""
            city, state, loc_raw = _parse_location(item)

            fp = make_fingerprint(company, title, city)

            # Skip within-batch duplicates
            if fp in seen_fingerprints:
                jobs_deduped += 1
                continue
            seen_fingerprints.add(fp)

            # Skip if already in DB
            existing = db.query(Job).filter(Job.external_id == fp).first()
            if existing:
                jobs_deduped += 1
                continue

            # Parse fields
            description  = item.get("description", "") or ""
            apply_url    = item.get("redirect_url", "") or ""
            date_posted  = _parse_date(item.get("created"))
            sal_min, sal_max, sal_disclosed = _parse_salary(item)
            emp_type     = item.get("contract_time", "") or ""
            if emp_type == "full_time":
                emp_type = "Full-time"
            elif emp_type == "part_time":
                emp_type = "Part-time"

            # Skip geocoding during scan for speed — distance calculated lazily
            dist_miles = None
            job_lat, job_lng = None, None

            # Fit score
            fit_score, breakdown = calculate_fit_score(
                title=title,
                description=description,
                salary_min=sal_min,
                salary_max=sal_max,
                experience_level=item.get("contract_type", ""),
                education_required="",
            )

            # Determine if hot (fit >= 85 and posted within 3 days)
            is_hot = False
            if fit_score >= 85 and date_posted:
                days_old = (date.today() - date_posted).days
                is_hot = days_old <= 3

            job = Job(
                external_id        = fp,
                title              = title,
                company            = company,
                location_city      = city,
                location_state     = state,
                location_raw       = loc_raw,
                location_lat       = job_lat,
                location_lng       = job_lng,
                distance_miles     = dist_miles,
                is_remote          = "remote" in (loc_raw + title + description).lower(),
                description        = description,
                salary_min         = sal_min,
                salary_max         = sal_max,
                salary_disclosed   = sal_disclosed,
                employment_type    = emp_type,
                source             = "Adzuna",
                source_urls        = json.dumps([apply_url]),
                apply_url          = apply_url,
                date_posted        = date_posted,
                fit_score          = fit_score,
                fit_score_breakdown= json.dumps(breakdown),
                is_hot             = is_hot,
                status             = "New",
            )
            db.add(job)
            jobs_new += 1

        db.commit()

        # Update scan log
        scan_log.completed_at   = datetime.now(timezone.utc)
        scan_log.jobs_fetched   = jobs_fetched
        scan_log.jobs_new       = jobs_new
        scan_log.jobs_deduplicated = jobs_deduped
        scan_log.status         = "success"
        db.commit()

        logger.info(f"Scan complete: {jobs_fetched} fetched, {jobs_new} new, {jobs_deduped} dupes")
        return {"jobs_fetched": jobs_fetched, "jobs_new": jobs_new, "jobs_deduplicated": jobs_deduped}

    except Exception as e:
        logger.error(f"Scan failed: {e}", exc_info=True)
        scan_log.completed_at = datetime.now(timezone.utc)
        scan_log.status       = "error"
        scan_log.error_message = str(e)
        db.commit()
        raise

    finally:
        db.close()
