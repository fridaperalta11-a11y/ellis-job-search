from dotenv import load_dotenv
import os

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ADZUNA_APP_ID     = os.getenv("ADZUNA_APP_ID", "")
ADZUNA_API_KEY    = os.getenv("ADZUNA_API_KEY", "")
JSEARCH_API_KEY   = os.getenv("JSEARCH_API_KEY", "")

DATABASE_URL = "sqlite:///./talentscope.db"

# Default candidate settings
DEFAULT_LOCATION        = "Houston, TX"
DEFAULT_RADIUS_MILES    = 50
DEFAULT_FIT_THRESHOLD   = 80
DEFAULT_FOLLOWUP_DAYS   = 7
DEFAULT_SCAN_SCHEDULE   = "daily"
