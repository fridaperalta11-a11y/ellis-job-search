"""
storage.py — load and save all persistent data using JSON files.
"""

import json
import os

DATA_DIR      = os.path.join(os.path.dirname(__file__), "data")
JOBS_FILE     = os.path.join(DATA_DIR, "jobs.json")
SETTINGS_FILE = os.path.join(DATA_DIR, "settings.json")
CACHE_FILE    = os.path.join(DATA_DIR, "search_cache.json")

os.makedirs(DATA_DIR, exist_ok=True)


# ── Saved Jobs ────────────────────────────────────────────────────────────────

def load_saved_jobs() -> list[dict]:
    if not os.path.exists(JOBS_FILE):
        return []
    with open(JOBS_FILE, "r") as f:
        return json.load(f)


def save_all_jobs(jobs: list[dict]) -> None:
    with open(JOBS_FILE, "w") as f:
        json.dump(jobs, f, indent=2)


def save_job(job: dict) -> bool:
    """Save a job. Returns False if duplicate (matched by link)."""
    jobs = load_saved_jobs()
    existing_links = {j["link"] for j in jobs}
    if job["link"] in existing_links:
        return False
    jobs.append({
        "title":   job.get("title", ""),
        "company": job.get("company", ""),
        "location": job.get("location", ""),
        "link":    job.get("link", ""),
        "status":  "Not Applied",
        "notes":   "",
    })
    save_all_jobs(jobs)
    return True


def update_job(link: str, status: str = None, notes: str = None) -> None:
    jobs = load_saved_jobs()
    for job in jobs:
        if job["link"] == link:
            if status is not None:
                job["status"] = status
            if notes is not None:
                job["notes"] = notes
            break
    save_all_jobs(jobs)


def delete_job(link: str) -> None:
    jobs = load_saved_jobs()
    jobs = [j for j in jobs if j["link"] != link]
    save_all_jobs(jobs)


# ── Search Cache ─────────────────────────────────────────────────────────────

def load_search_cache() -> list[dict]:
    if not os.path.exists(CACHE_FILE):
        return []
    with open(CACHE_FILE, "r") as f:
        return json.load(f)


def save_search_cache(jobs: list[dict]) -> None:
    with open(CACHE_FILE, "w") as f:
        json.dump(jobs, f, indent=2)


# ── Settings (cover image + quote) ───────────────────────────────────────────

def load_settings() -> dict:
    defaults = {"cover_image": None, "quote": "", "avatar": None, "cover_position": "center"}
    if not os.path.exists(SETTINGS_FILE):
        return defaults
    with open(SETTINGS_FILE, "r") as f:
        data = json.load(f)
    # Ensure all keys exist
    for k, v in defaults.items():
        data.setdefault(k, v)
    return data


def save_settings(settings: dict) -> None:
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=2)


def update_cover_image(path: str) -> None:
    s = load_settings()
    s["cover_image"] = path
    save_settings(s)


def update_avatar(path: str) -> None:
    s = load_settings()
    s["avatar"] = path
    save_settings(s)


def update_cover_position(position: str) -> None:
    s = load_settings()
    s["cover_position"] = position
    save_settings(s)


def update_quote(quote: str) -> None:
    s = load_settings()
    s["quote"] = quote
    save_settings(s)
