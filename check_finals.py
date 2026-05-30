import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))
from database import get_conn
conn = get_conn()

print("Final-week non-consolation games per season:")
for r in conn.execute("""
    SELECT m.season, COUNT(*) as games
    FROM matchups m
    JOIN leagues l ON m.league_key=l.league_key
    WHERE m.is_playoffs=1 AND m.is_consolation=0 AND m.week=l.end_week
    GROUP BY m.season ORDER BY m.season
""").fetchall():
    flag = " <-- WRONG" if r['games'] != 1 else ""
    print(f"  {r['season']}: {r['games']} games{flag}")
conn.close()
