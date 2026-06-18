import os
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).parent.parent
load_dotenv(ROOT / ".env")

ANTHROPIC_API_KEY: str = os.environ["ANTHROPIC_API_KEY"]
MODEL: str = os.getenv("SRAI_MODEL", "claude-sonnet-4-6")

DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)
STATE_FILE = DATA_DIR / "state.json"
LOGS_DIR = DATA_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)

GOOGLE_AUTH_DIR = ROOT / "google_auth"
GOOGLE_CREDS_FILE = GOOGLE_AUTH_DIR / "credentials.json"
GOOGLE_TOKEN_FILE = GOOGLE_AUTH_DIR / "token.json"
GOOGLE_SCOPES = [
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/gmail.modify",
]

CALENDAR_ID: str = os.getenv("SRAI_CALENDAR_ID", "primary")
PERSONAL_EMAIL: str = os.getenv("SRAI_PERSONAL_EMAIL", "")
TIMEZONE: str = os.getenv("SRAI_TIMEZONE", "America/Los_Angeles")
