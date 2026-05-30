import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))
from database import get_conn

conn = get_conn()

current_season = None
for r in conn.execute("""
    SELECT t.season, o.nickname, t.name, t.manager_name
    FROM teams t
    JOIN team_owner_map m ON t.team_key=m.team_key
    JOIN owners o ON m.owner_id=o.owner_id
    ORDER BY t.season, o.nickname
""").fetchall():
    if r["season"] != current_season:
        current_season = r["season"]
        print(f"\n=== {current_season} ===")
        print(f"  {'Owner':<12} {'Team Name':<35} Manager")
        print(f"  {'-'*12} {'-'*35} {'-'*20}")
    print(f"  {r['nickname']:<12} {r['name']:<35} {r['manager_name']}")

conn.close()
