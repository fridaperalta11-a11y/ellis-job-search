from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime


class CandidateProfileUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    location_address: Optional[str] = None
    max_radius_miles: Optional[int] = None
    salary_floor_annual: Optional[float] = None
    salary_max_annual: Optional[float] = None
    salary_goal_annual: Optional[float] = None
    salary_input_mode: Optional[str] = None
    work_type_preferences: Optional[str] = None
    employment_type_preferences: Optional[str] = None
    excluded_industries: Optional[str] = None
    career_goal_short_term: Optional[str] = None
    career_goal_long_term: Optional[str] = None
    resume_raw_text: Optional[str] = None
    resume_parsed_profile: Optional[str] = None
    alert_fit_score_threshold: Optional[int] = None
    followup_reminder_days: Optional[int] = None
    scan_schedule: Optional[str] = None


class ResumeVersionCreate(BaseModel):
    name: str
    raw_text: str
    is_active: bool = False


class JobStatusUpdate(BaseModel):
    status: str


class JobStarUpdate(BaseModel):
    is_starred: bool


class JobNotesUpdate(BaseModel):
    notes: str


class JobTimelineUpdate(BaseModel):
    date_applied: Optional[date] = None
    date_followup_due: Optional[date] = None
    date_interview: Optional[date] = None
    date_decision: Optional[date] = None
    recruiter_name: Optional[str] = None
    recruiter_email: Optional[str] = None
    recruiter_linkedin: Optional[str] = None
    resume_version_id: Optional[int] = None


class JobOfferUpdate(BaseModel):
    offer_details: str


class ManualJobInput(BaseModel):
    url: Optional[str] = None
    raw_text: Optional[str] = None


class ParseResumeRequest(BaseModel):
    raw_text: str
