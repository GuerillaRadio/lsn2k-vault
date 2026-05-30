import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))
from database import get_conn

conn = get_conn()

def oid(nick):
    return conn.execute("SELECT owner_id FROM owners WHERE nickname=?", (nick,)).fetchone()[0]

def map_by_name(pattern, nick, season=None):
    sql = "SELECT team_key FROM teams WHERE name LIKE ?"
    params = [f"%{pattern}%"]
    if season:
        sql += " AND season=?"
        params.append(season)
    for r in conn.execute(sql, params).fetchall():
        conn.execute("INSERT OR REPLACE INTO team_owner_map (team_key,owner_id) VALUES (?,?)",
                     (r[0], oid(nick)))
        print(f"  Mapped: {r[0]} -> {nick}")

# 2007 mappings (manager names now visible)
map_by_name("Amanda",           "James",   2007)
map_by_name("Anal Trauma",      "Hippe",   2007)
map_by_name("succinylcholine",  "Chou",    2007)
map_by_name("Lick My Love Pump","Dusty",   2007)

conn.commit()

unmapped = conn.execute("""
    SELECT t.season, t.name, t.manager_name
    FROM teams t LEFT JOIN team_owner_map m ON t.team_key=m.team_key
    WHERE m.owner_id IS NULL ORDER BY t.season, t.name
""").fetchall()

if unmapped:
    print(f"\n{len(unmapped)} still unmapped:")
    for r in unmapped:
        print(f"  {r[0]}  {r[1]:<30}  {r[2]}")
else:
    total = conn.execute("SELECT COUNT(*) FROM team_owner_map").fetchone()[0]
    print(f"\nAll {total} teams mapped!")

conn.close()
