import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))
from database import get_conn

conn = get_conn()

print("Seasons where any owner has more than one team:\n")
found = False
for r in conn.execute("""
    SELECT t.season, o.nickname, COUNT(*) as n,
           GROUP_CONCAT(t.name || ' [' || COALESCE(t.manager_name,'?') || ']', ' / ') as teams
    FROM teams t
    JOIN team_owner_map m ON t.team_key=m.team_key
    JOIN owners o ON m.owner_id=o.owner_id
    GROUP BY t.season, o.owner_id
    HAVING n > 1
    ORDER BY t.season, o.nickname
""").fetchall():
    print(f"  {r['season']} — {r['nickname']}: {r['teams']}")
    found = True

if not found:
    print("  None found — all owners have exactly one team per season.")

conn.close()
