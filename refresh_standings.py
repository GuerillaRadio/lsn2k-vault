"""Re-fetch standings for all seasons, then rebuild aggregates."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))
from database import get_conn
from fetcher import fetch_standings
from auth import get_oauth

conn = get_conn()
oauth = get_oauth()

leagues = conn.execute("SELECT league_key, season FROM leagues ORDER BY season").fetchall()
conn.close()

print(f"Re-fetching standings for {len(leagues)} seasons...")
for row in leagues:
    conn = get_conn()
    try:
        fetch_standings(oauth, row["league_key"], row["season"], conn)
        # Verify
        sample = conn.execute(
            "SELECT rank, wins, losses FROM standings WHERE season=? LIMIT 1",
            (row["season"],)
        ).fetchone()
        if sample and sample["wins"] > 0:
            print(f"  {row['season']}: OK (sample: {sample['wins']}W-{sample['losses']}L rank {sample['rank']})")
        else:
            print(f"  {row['season']}: still empty")
    except Exception as e:
        print(f"  {row['season']}: ERROR - {e}")
    finally:
        conn.close()

print("\nRebuilding aggregates...")
import subprocess
subprocess.run([sys.executable, "build_aggregates.py"])
