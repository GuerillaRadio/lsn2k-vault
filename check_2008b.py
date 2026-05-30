import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))
from database import get_conn

conn = get_conn()

print("All 2008 teams and their mapped owners:")
for r in conn.execute("""
    SELECT t.team_key, t.name, t.manager_name, o.nickname
    FROM teams t
    LEFT JOIN team_owner_map m ON t.team_key=m.team_key
    LEFT JOIN owners o ON m.owner_id=o.owner_id
    WHERE t.season=2008 ORDER BY o.nickname
""").fetchall():
    print(f"  {r['nickname']:>10}  |  {r['name']:<30}  |  {r['manager_name']}")

print("\nOwners with multiple 2008 teams:")
for r in conn.execute("""
    SELECT o.nickname, COUNT(*) as n, GROUP_CONCAT(t.name, ', ') as teams
    FROM teams t
    JOIN team_owner_map m ON t.team_key=m.team_key
    JOIN owners o ON m.owner_id=o.owner_id
    WHERE t.season=2008
    GROUP BY o.owner_id HAVING n > 1
""").fetchall():
    print(f"  {r['nickname']}: {r['n']} teams — {r['teams']}")

conn.close()
