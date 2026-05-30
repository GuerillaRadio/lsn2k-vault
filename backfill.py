"""One-time backfill of all seasons into the local database."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from database import init_db, get_conn
from fetcher import fetch_season
from config import LEAGUES

INACCESSIBLE = set()  # all leagues accessible

if __name__ == "__main__":
    init_db()
    conn = get_conn()
    already_done = {
        r[0] for r in conn.execute("SELECT league_key FROM leagues").fetchall()
    }
    conn.close()

    todo = [e for e in LEAGUES if e["league_key"] not in already_done
            and e["league_key"] not in INACCESSIBLE]

    print(f"\nBackfilling {len(todo)} seasons (skipping {len(already_done)} already loaded)...\n")
    for entry in todo:
        try:
            fetch_season(entry["league_key"], entry["season"])
        except Exception as e:
            print(f"  ERROR on {entry['season']}: {e}")
            continue

    print("\nBackfill complete.")
