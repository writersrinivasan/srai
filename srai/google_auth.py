from __future__ import annotations

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from srai.config import GOOGLE_CREDS_FILE, GOOGLE_TOKEN_FILE, GOOGLE_SCOPES


def get_credentials() -> Credentials:
    creds: Credentials | None = None
    if GOOGLE_TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(GOOGLE_TOKEN_FILE), GOOGLE_SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not GOOGLE_CREDS_FILE.exists():
                raise FileNotFoundError(
                    f"Missing {GOOGLE_CREDS_FILE}. "
                    "Download OAuth 2.0 Desktop credentials from Google Cloud Console "
                    "and save as google_auth/credentials.json"
                )
            flow = InstalledAppFlow.from_client_secrets_file(str(GOOGLE_CREDS_FILE), GOOGLE_SCOPES)
            creds = flow.run_local_server(port=0)
        GOOGLE_TOKEN_FILE.parent.mkdir(exist_ok=True)
        with open(GOOGLE_TOKEN_FILE, "w") as f:
            f.write(creds.to_json())
    return creds


def calendar_service():
    return build("calendar", "v3", credentials=get_credentials(), cache_discovery=False)


def gmail_service():
    return build("gmail", "v1", credentials=get_credentials(), cache_discovery=False)
