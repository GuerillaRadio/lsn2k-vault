import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))
from database import get_conn
conn = get_conn()
total = conn.execute("SELECT COUNT(*) FROM player_weekly_stats WHERE stats_json IS NOT NULL AND stats_json != '{}'").fetchone()[0]
print(f"Rows with stats_json: {total:,}")
print("\nBy season:")
for r in conn.execute("SELECT season, COUNT(*) as n FROM player_weekly_stats WHERE stats_json IS NOT NULL AND stats_json != '{}' GROUP BY season ORDER BY season").fetchall():
    print(f"  {r['season']}: {r['n']:,}")
conn.close()
