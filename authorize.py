"""
Two-step Yahoo authorization.

Step 1 (no args): prints the authorization URL — open it, approve, copy the code from the URL bar.
Step 2 (--code XXX): exchanges the code for tokens and saves them.
"""

import sys
import json
import time
import base64
from pathlib import Path
from urllib.parse import urlencode

import requests
from dotenv import load_dotenv
import os

load_dotenv(Path(__file__).parent / ".env")

CLIENT_ID = os.getenv("YAHOO_CLIENT_ID")
CLIENT_SECRET = os.getenv("YAHOO_CLIENT_SECRET")
REDIRECT_URI = "https://localhost"
TOKEN_URL = "https://api.login.yahoo.com/oauth2/get_token"
AUTH_URL = "https://api.login.yahoo.com/oauth2/request_auth"
OAUTH_FILE = Path(__file__).parent / "data" / "oauth.json"


def print_auth_url():
    params = {
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
    }
    url = AUTH_URL + "?" + urlencode(params)
    print("\n=== Step 1: Open this URL in your browser ===")
    print(url)
    print("\nAfter approving, your browser will go to a broken https://localhost page.")
    print("Copy the value after 'code=' in the URL bar.")
    print("\nThen run:  python authorize.py --code PASTE_CODE_HERE\n")


def exchange_code(code: str):
    encoded = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()
    headers = {
        "Authorization": f"Basic {encoded}",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
    }
    resp = requests.post(TOKEN_URL, headers=headers, data=data)
    if not resp.ok:
        print(f"Error {resp.status_code}: {resp.text}")
        sys.exit(1)

    tokens = resp.json()
    # Save in yahoo_oauth-compatible format
    payload = {
        "consumer_key": CLIENT_ID,
        "consumer_secret": CLIENT_SECRET,
        "access_token": tokens["access_token"],
        "refresh_token": tokens["refresh_token"],
        "token_type": tokens.get("token_type", "bearer"),
        "token_time": time.time(),
    }
    OAUTH_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OAUTH_FILE, "w") as f:
        json.dump(payload, f, indent=2)
    print(f"Tokens saved to {OAUTH_FILE}")
    print("Now run:  python login.py")


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--code":
        exchange_code(sys.argv[2])
    else:
        print_auth_url()
