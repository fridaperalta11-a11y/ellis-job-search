"""
Fit Score engine — scores a job against the candidate profile.

5 dimensions (weights must sum to 1.0):
  Skills Match      40%
  Title Match       20%
  Experience Level  20%
  Education Match   10%
  Salary Match      10%

Returns a score 0–100 and a breakdown dict.
"""
import re


# ── Frida's profile constants (pulled from resume / settings) ─────────────────

FRIDA_SKILLS = [
    "power bi", "excel", "python", "spss", "powerpoint",
    "microsoft office", "google workspace", "canva",
    "uroChart", "athenahealth", "emr",
    "data analysis", "kpi", "dashboard", "reporting",
    "project management", "coordination", "operations",
    "bilingual", "spanish", "english",
    "hipaa", "compliance", "documentation",
    "variance analysis", "financial dashboard",
    "cash handling", "client relations", "sales",
    "needs assessment", "active listening",
    "process mapping", "workflow",
]

FRIDA_TITLES = [
    "business analyst", "data analyst", "operations analyst",
    "systems analyst", "research analyst", "program analyst",
    "epic business analyst", "erp business analyst",
    "project analyst", "teller", "banker", "regional banker",
    "financial solutions advisor", "personal banker",
    "financial advisor", "banking associate",
]

FRIDA_EDUCATION_KEYWORDS = [
    "bachelor", "b.a.", "ba ", "sociology", "university of texas",
    "ut austin", "associate", "high school",
]

TARGET_EXPERIENCE_LEVELS = {"entry", "mid", "associate", "junior", ""}

SALARY_FLOOR   = 40_000
SALARY_MAX     = 120_000
SALARY_GOAL    = 70_000


# ── Helpers ───────────────────────────────────────────────────────────────────

def _lower(text: str) -> str:
    return (text or "").lower()


def _skill_hits(text: str) -> int:
    t = _lower(text)
    return sum(1 for s in FRIDA_SKILLS if s in t)


def _title_match(job_title: str, job_desc: str) -> float:
    combined = _lower(job_title) + " " + _lower(job_desc)
    hits = sum(1 for t in FRIDA_TITLES if t in combined)
    return min(hits / 2, 1.0)   # 2 hits = full score


def _experience_match(level: str) -> float:
    lvl = _lower(level).strip()
    if not lvl or lvl in TARGET_EXPERIENCE_LEVELS:
        return 1.0
    if "senior" in lvl or "lead" in lvl or "manager" in lvl or "director" in lvl:
        return 0.2
    return 0.7


def _education_match(edu_required: str, job_desc: str) -> float:
    combined = _lower(edu_required) + " " + _lower(job_desc)
    # Reject if PhD / JD / MD / MBA required
    if re.search(r"\b(phd|doctorate|j\.?d|m\.?d|mba)\b", combined):
        return 0.3
    # Full match if bachelor's or associate's is sufficient or not specified
    if re.search(r"\b(bachelor|associate|high school|ged|not required|preferred)\b", combined):
        return 1.0
    if re.search(r"\b(master|graduate degree)\b", combined):
        return 0.5
    return 0.85  # unspecified — assume OK


def _salary_match(sal_min: float | None, sal_max: float | None) -> float:
    if sal_min is None and sal_max is None:
        return 0.75   # not disclosed — partial credit

    mid = None
    if sal_min and sal_max:
        mid = (sal_min + sal_max) / 2
    elif sal_max:
        mid = sal_max
    elif sal_min:
        mid = sal_min

    if mid is None:
        return 0.75

    if mid < SALARY_FLOOR:
        return 0.1
    if mid >= SALARY_GOAL:
        return 1.0
    # Linear scale between floor and goal
    return (mid - SALARY_FLOOR) / (SALARY_GOAL - SALARY_FLOOR)


# ── Public API ────────────────────────────────────────────────────────────────

def calculate_fit_score(
    title: str,
    description: str,
    salary_min: float | None,
    salary_max: float | None,
    experience_level: str,
    education_required: str,
) -> tuple[float, dict]:
    """
    Returns (score_0_to_100, breakdown_dict).
    """
    desc_and_title = f"{title} {description}"

    skill_hits = _skill_hits(desc_and_title)
    skill_possible = max(len(FRIDA_SKILLS) * 0.3, 1)   # expect ~30% hit rate for a good match
    skills_raw = min(skill_hits / skill_possible, 1.0)

    title_raw  = _title_match(title, description)
    exp_raw    = _experience_match(experience_level)
    edu_raw    = _education_match(education_required, description)
    sal_raw    = _salary_match(salary_min, salary_max)

    score = (
        skills_raw * 0.40 +
        title_raw  * 0.20 +
        exp_raw    * 0.20 +
        edu_raw    * 0.10 +
        sal_raw    * 0.10
    ) * 100

    breakdown = {
        "skills":     round(skills_raw * 100),
        "title":      round(title_raw  * 100),
        "experience": round(exp_raw    * 100),
        "education":  round(edu_raw    * 100),
        "salary":     round(sal_raw    * 100),
        "total":      round(score),
        "skill_hits": skill_hits,
    }

    return round(score, 1), breakdown
