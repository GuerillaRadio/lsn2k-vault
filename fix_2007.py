"""Delete bad 2007 data and re-fetch the correct league."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))
from database import get_conn, init_db
from fetcher import fetch_season

BAD_KEY  = "175.l.20473"
GOOD_KEY = "176.l.20473"

conn = get_conn()
print("Deleting bad 2007 data...")
for table, col in [
    ("player_weekly_stats", "league_key"),
    ("roster_slots",        "league_key"),
    ("transaction_players", "transaction_key"),
    ("transactions",        "league_key"),
    ("matchups",            "league_key"),
    ("draft_picks",         "league_key"),
    ("standings",           "league_key"),
    ("scoring_settings",    "league_key"),
    ("roster_positions",    "league_key"),
    ("team_owner_map",      "team_key"),
]:
    if col == "transaction_key":
        conn.execute(f"""
            DELETE FROM {table} WHERE transaction_key IN (
                SELECT transaction_key FROM transactions WHERE league_key=?
            )""", (BAD_KEY,))
    elif col == "team_key":
        conn.execute(f"""
            DELETE FROM {table} WHERE team_key IN (
                SELECT team_key FROM teams WHERE league_key=?
            )""", (BAD_KEY,))
    else:
        conn.execute(f"DELETE FROM {table} WHERE {col}=?", (BAD_KEY,))

conn.execute("DELETE FROM teams WHERE league_key=?", (BAD_KEY,))
conn.execute("DELETE FROM leagues WHERE league_key=?", (BAD_KEY,))
conn.commit()
conn.close()
print("Done. Fetching correct 2007 league...")
fetch_season(GOOD_KEY, 2007)
print("2007 re-fetch complete.")
