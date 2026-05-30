"""Re-fetch transactions and rosters for 2011 and 2017."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))
from database import get_conn
from auth import get_oauth
from fetcher import fetch_transactions, fetch_rosters_and_stats, fetch_players

oauth = get_oauth()

SEASONS = [
    {"season": 2011, "league_key": "257.l.2106",  "start_week": 1, "end_week": 16},
    {"season": 2017, "league_key": "371.l.69482", "start_week": 1, "end_week": 16},
]

for s in SEASONS:
    season = s["season"]
    league_key = s["league_key"]
    print(f"\n--- {season} ({league_key}) ---")

    conn = get_conn()

    # Clear existing incomplete rosters and stats for this season
    print("  Clearing existing roster/stats data...")
    conn.execute("DELETE FROM player_weekly_stats WHERE league_key=?", (league_key,))
    conn.execute("DELETE FROM roster_slots WHERE league_key=?", (league_key,))
    conn.execute("DELETE FROM transactions WHERE league_key=?", (league_key,))
    conn.execute("DELETE FROM transaction_players WHERE transaction_key IN (SELECT transaction_key FROM transactions WHERE league_key=?)", (league_key,))
    conn.commit()

    print("  Re-fetching rosters + stats...")
    fetch_rosters_and_stats(oauth, league_key, season, s["start_week"], s["end_week"], conn)

    print("  Re-fetching transactions...")
    fetch_transactions(oauth, league_key, season, conn)

    conn.close()
    print(f"  Done.")

print("\nRebuilding aggregates...")
import subprocess
subprocess.run([sys.executable, "build_aggregates.py"])
print("All done.")
