"""
Weekly update — pulls latest data for the active season.
Runs year-round via Task Scheduler but exits early outside NFL season (Sept-Feb).
"""
import sys
from pathlib import Path
from datetime import date

sys.path.insert(0, str(Path(__file__).parent / "src"))

# Only run during NFL season (September through February)
today = date.today()
in_season = today.month >= 9 or today.month <= 2
if not in_season:
    print(f"Off-season ({today.strftime('%B %d')}). Skipping update.")
    sys.exit(0)

print(f"In-season update starting ({today.strftime('%B %d, %Y')})...")

from database import get_conn
from fetcher import fetch_season
from config import LEAGUES

conn = get_conn()

# Find the most recent non-finished season
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

# Rebuild aggregates and final standings
print("Rebuilding aggregates...")
import subprocess
subprocess.run([sys.executable, str(Path(__file__).parent / "build_aggregates.py")])
subprocess.run([sys.executable, str(Path(__file__).parent / "build_final_standings.py")])
subprocess.run([sys.executable, str(Path(__file__).parent / "rebuild_trade_summary.py")])
subprocess.run([sys.executable, str(Path(__file__).parent / "build_all_analytics.py")])

# Push to Turso
print("Syncing to Turso...")
subprocess.run([sys.executable, str(Path(__file__).parent / "push_to_turso.py")])

print("Weekly update complete.")
