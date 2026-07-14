from sqlalchemy import (
    Column, Integer, Text, Float, Boolean, Date, DateTime, ForeignKey
)
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from database import Base


class CandidateProfile(Base):
    __tablename__ = "candidate_profile"

    id                          = Column(Integer, primary_key=True, default=1)
    name                        = Column(Text, default="")
    email                       = Column(Text, default="")
    location_address            = Column(Text, default="Houston, TX")
    location_lat                = Column(Float, nullable=True)
    location_lng                = Column(Float, nullable=True)
    max_radius_miles            = Column(Integer, default=50)
    salary_floor_annual         = Column(Float, nullable=True)
    salary_max_annual           = Column(Float, nullable=True)
    salary_goal_annual          = Column(Float, nullable=True)
    salary_input_mode           = Column(Text, default="annual")
    work_type_preferences       = Column(Text, default='["On-site", "Hybrid", "Remote"]')
    employment_type_preferences = Column(Text, default='["Full-time", "Part-time"]')
    excluded_industries         = Column(Text, default="[]")
    career_goal_short_term      = Column(Text, default="")
    career_goal_long_term       = Column(Text, default="")
    resume_raw_text             = Column(Text, default="")
    resume_parsed_profile       = Column(Text, default="{}")
    alert_fit_score_threshold   = Column(Integer, default=80)
    followup_reminder_days      = Column(Integer, default=7)
    scan_schedule               = Column(Text, default="daily")
    created_at                  = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at                  = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                                         onupdate=lambda: datetime.now(timezone.utc))


class ResumeVersion(Base):
    __tablename__ = "resume_version"

    id             = Column(Integer, primary_key=True, autoincrement=True)
    name           = Column(Text, nullable=False)
    raw_text       = Column(Text, default="")
    parsed_profile = Column(Text, default="{}")
    is_active      = Column(Boolean, default=False)
    created_at     = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    jobs = relationship("Job", back_populates="resume_version")


class Job(Base):
    __tablename__ = "job"

    id                  = Column(Integer, primary_key=True, autoincrement=True)
    external_id         = Column(Text, unique=True, nullable=False)
    title               = Column(Text, default="")
    company             = Column(Text, default="")
    location_city       = Column(Text, default="")
    location_state      = Column(Text, default="")
    location_raw        = Column(Text, default="")
    location_lat        = Column(Float, nullable=True)
    location_lng        = Column(Float, nullable=True)
    distance_miles      = Column(Float, nullable=True)
    is_remote           = Column(Boolean, default=False)
    is_hybrid           = Column(Boolean, default=False)
    description         = Column(Text, default="")
    salary_min          = Column(Float, nullable=True)
    salary_max          = Column(Float, nullable=True)
    salary_raw          = Column(Text, default="")
    salary_disclosed    = Column(Boolean, default=False)
    employment_type     = Column(Text, default="")
    experience_level    = Column(Text, default="")
    education_required  = Column(Text, default="")
    source              = Column(Text, default="")
    source_urls         = Column(Text, default="[]")
    apply_url           = Column(Text, default="")
    date_posted         = Column(Date, nullable=True)
    is_hot              = Column(Boolean, default=False)
    is_stale            = Column(Boolean, default=False)
    fit_score           = Column(Float, nullable=True)
    fit_score_breakdown = Column(Text, default="{}")
    recruiters_take     = Column(Text, default="")
    gap_analysis        = Column(Text, default="[]")
    status              = Column(Text, default="New")
    is_starred          = Column(Boolean, default=False)
    is_archived         = Column(Boolean, default=False)
    notes               = Column(Text, default="")
    interview_prep_notes = Column(Text, default="")
    resume_version_id   = Column(Integer, ForeignKey("resume_version.id"), nullable=True)
    cover_letter        = Column(Text, default="")
    date_applied        = Column(Date, nullable=True)
    date_followup_due   = Column(Date, nullable=True)
    date_interview      = Column(Date, nullable=True)
    date_decision       = Column(Date, nullable=True)
    recruiter_name      = Column(Text, default="")
    recruiter_email     = Column(Text, default="")
    recruiter_linkedin  = Column(Text, default="")
    offer_details       = Column(Text, default="{}")
    similar_job_ids     = Column(Text, default="[]")
    created_at          = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at          = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                                  onupdate=lambda: datetime.now(timezone.utc))

    resume_version = relationship("ResumeVersion", back_populates="jobs")


class ScanLog(Base):
    __tablename__ = "scan_log"

    id               = Column(Integer, primary_key=True, autoincrement=True)
    started_at       = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at     = Column(DateTime, nullable=True)
    jobs_fetched     = Column(Integer, default=0)
    jobs_new         = Column(Integer, default=0)
    jobs_deduplicated = Column(Integer, default=0)
    sources_used     = Column(Text, default="[]")
    status           = Column(Text, default="success")
    error_message    = Column(Text, default="")


class Alert(Base):
    __tablename__ = "alert"

    id         = Column(Integer, primary_key=True, autoincrement=True)
    message    = Column(Text, default="")
    job_count  = Column(Integer, default=0)
    is_read    = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
