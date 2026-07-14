from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager
from sqlalchemy.orm import Session
import json
import os
import re
from pathlib import Path

from database import engine, Base, SessionLocal
from models import CandidateProfile, Alert, Job
from schemas import CandidateProfileUpdate
from scheduler import start_scheduler, stop_scheduler
from config import DEFAULT_LOCATION, DEFAULT_RADIUS_MILES, DEFAULT_FIT_THRESHOLD, DEFAULT_FOLLOWUP_DAYS
from routers import scan as scan_router

import models  # noqa — ensures all models register with Base


def seed_profile(db: Session):
    """Create the single candidate profile row if it doesn't exist."""
    profile = db.query(CandidateProfile).filter(CandidateProfile.id == 1).first()
    if not profile:
        profile = CandidateProfile(
            id=1,
            location_address=DEFAULT_LOCATION,
            max_radius_miles=DEFAULT_RADIUS_MILES,
            alert_fit_score_threshold=DEFAULT_FIT_THRESHOLD,
            followup_reminder_days=DEFAULT_FOLLOWUP_DAYS,
        )
        db.add(profile)
        db.commit()


async def scheduled_scan():
    """Scheduled daily scan job."""
    from services.ingestion import run_scan
    try:
        await run_scan()
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Scheduled scan error: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables
    Base.metadata.create_all(bind=engine)

    # Seed candidate profile
    db = SessionLocal()
    try:
        seed_profile(db)
    finally:
        db.close()

    # Start scheduler
    start_scheduler(scheduled_scan)

    yield

    stop_scheduler()


app = FastAPI(title="Ellis", lifespan=lifespan)

app.include_router(scan_router.router)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Custom Jinja2 filter: parse JSON strings in templates
def from_json(value, default=None):
    try:
        return json.loads(value)
    except Exception:
        return default if default is not None else []

templates.env.filters["from_json"] = from_json


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/")
async def scanner_home(request: Request):
    db = SessionLocal()
    try:
        profile = db.query(CandidateProfile).filter(CandidateProfile.id == 1).first()
        unread_alerts = db.query(Alert).filter(Alert.is_read == False).count()

        # All non-archived jobs, newest first
        jobs = (
            db.query(Job)
            .filter(Job.is_archived == False)
            .order_by(Job.date_posted.desc(), Job.created_at.desc())
            .all()
        )

        # Top 5 by fit score, minimum score 70
        top5 = (
            db.query(Job)
            .filter(Job.is_archived == False, Job.fit_score >= 70)
            .order_by(Job.fit_score.desc())
            .limit(5)
            .all()
        )
    finally:
        db.close()

    return templates.TemplateResponse("scanner.html", {
        "request": request,
        "profile": profile,
        "unread_alerts": unread_alerts,
        "jobs": jobs,
        "top5": top5,
        "page": "scanner",
    })


@app.get("/applications")
async def applications(request: Request):
    db = SessionLocal()
    try:
        profile = db.query(CandidateProfile).filter(CandidateProfile.id == 1).first()
        unread_alerts = db.query(Alert).filter(Alert.is_read == False).count()
    finally:
        db.close()

    return templates.TemplateResponse("applications.html", {
        "request": request,
        "profile": profile,
        "unread_alerts": unread_alerts,
        "page": "applications",
    })


@app.get("/analytics")
async def analytics(request: Request):
    db = SessionLocal()
    try:
        profile = db.query(CandidateProfile).filter(CandidateProfile.id == 1).first()
        unread_alerts = db.query(Alert).filter(Alert.is_read == False).count()
    finally:
        db.close()

    return templates.TemplateResponse("analytics.html", {
        "request": request,
        "profile": profile,
        "unread_alerts": unread_alerts,
        "page": "analytics",
    })


@app.get("/map")
async def map_view(request: Request):
    db = SessionLocal()
    try:
        profile = db.query(CandidateProfile).filter(CandidateProfile.id == 1).first()
        unread_alerts = db.query(Alert).filter(Alert.is_read == False).count()
    finally:
        db.close()

    return templates.TemplateResponse("map.html", {
        "request": request,
        "profile": profile,
        "unread_alerts": unread_alerts,
        "page": "map",
    })


@app.get("/settings")
async def settings(request: Request):
    db = SessionLocal()
    try:
        profile = db.query(CandidateProfile).filter(CandidateProfile.id == 1).first()
        unread_alerts = db.query(Alert).filter(Alert.is_read == False).count()
    finally:
        db.close()

    return templates.TemplateResponse("settings.html", {
        "request": request,
        "profile": profile,
        "unread_alerts": unread_alerts,
        "page": "settings",
    })


# ── API: Profile ───────────────────────────────────────────────────────────────

@app.patch("/api/profile")
async def update_profile(data: CandidateProfileUpdate):
    db = SessionLocal()
    try:
        profile = db.query(CandidateProfile).filter(CandidateProfile.id == 1).first()
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        for field, value in data.model_dump(exclude_none=True).items():
            setattr(profile, field, value)
        db.commit()
        db.refresh(profile)
        return {"ok": True}
    finally:
        db.close()


# ── API: Keys (writes to .env file) ───────────────────────────────────────────

_ENV_PATH = Path(__file__).parent / ".env"
_KEY_MAP = {
    "anthropic_key":  "ANTHROPIC_API_KEY",
    "adzuna_app_id":  "ADZUNA_APP_ID",
    "adzuna_api_key": "ADZUNA_API_KEY",
    "jsearch_api_key":"JSEARCH_API_KEY",
}

@app.post("/api/keys")
async def save_keys(request: Request):
    body = await request.json()

    # Read existing .env lines
    lines = []
    if _ENV_PATH.exists():
        lines = _ENV_PATH.read_text().splitlines()

    for field, env_var in _KEY_MAP.items():
        value = body.get(field, "").strip()
        if not value:
            continue
        # Replace existing line or append
        pattern = re.compile(rf"^{re.escape(env_var)}\s*=")
        replaced = False
        for i, line in enumerate(lines):
            if pattern.match(line):
                lines[i] = f"{env_var}={value}"
                replaced = True
                break
        if not replaced:
            lines.append(f"{env_var}={value}")

    _ENV_PATH.write_text("\n".join(lines) + "\n")
    return {"ok": True}
