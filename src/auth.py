"""Yahoo Fantasy Sports OAuth 2.0 authentication via yahoo_oauth."""

import os
from pathlib import Path
from dotenv import load_dotenv
from yahoo_oauth import OAuth2

load_dotenv(Path(__file__).parent.parent / ".env")

CLIENT_ID = os.getenv("YAHOO_CLIENT_ID")
CLIENT_SECRET = os.getenv("YAHOO_CLIENT_SECRET")
OAUTH_FILE = Path(__file__).parent.parent / "data" / "oauth.json"
FANTASY_BASE = "https://fantasysports.yahooapis.com/fantasy/v2"


def get_oauth() -> OAuth2:
    """Return an authenticated OAuth2 session, running the auth flow if needed."""
    OAUTH_FILE.parent.mkdir(parents=True, exist_ok=True)
    oauth = OAuth2(
        CLIENT_ID,
        CLIENT_SECRET,
        from_file=str(OAUTH_FILE) if OAUTH_FILE.exists() else None,
        callback_uri="https://localhost",
    )
    return oauth
