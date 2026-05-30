"""Weekly cron job — updates the current active season's data."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from database import get_conn
from fetcher import fetch_season
from config import LEAGUES

if __name__ == "__main__":
    conn = get_conn()

    # Find the most recent non-finished season we have (or the last one)
    active = None
    for entry in reversed(LEAGUES):
        row = conn.execute(
            "SELECT is_finished FROM leagues WHERE league_key=?",
            (entry["league_key"],)
        ).fetchone()
        if row is None or not row["is_finished"]:
            active = entry
            break

    conn.close()

    if not active:
        print("No active season found.")
        sys.exit(0)

    print(f"Updating {active['season']} ({active['league_key']})...")
    fetch_season(active["league_key"], active["season"])
    print("Done.")
