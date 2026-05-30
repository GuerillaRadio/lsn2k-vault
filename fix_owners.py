import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))
from database import get_conn

conn = get_conn()

# Add new owners
conn.execute("INSERT OR IGNORE INTO owners (full_name, nickname, yahoo_names) VALUES (?,?,?)",
             ("Adam Kroeger", "Kroeger", None))
conn.execute("INSERT OR IGNORE INTO owners (full_name, nickname, yahoo_names) VALUES (?,?,?)",
             ("Jon Parris", "Parris", "Jon"))
conn.commit()

def oid(nick):
    return conn.execute("SELECT owner_id FROM owners WHERE nickname=?", (nick,)).fetchone()[0]

def map_by_name(name_pattern, nick, season=None):
    sql = "SELECT team_key FROM teams WHERE name LIKE ?"
    params = [f"%{name_pattern}%"]
    if season:
        sql += " AND season=?"
        params.append(season)
    for r in conn.execute(sql, params).fetchall():
        conn.execute("INSERT OR REPLACE INTO team_owner_map (team_key,owner_id) VALUES (?,?)",
                     (r[0], oid(nick)))

# Fix 2005 Bye = Falk
map_by_name("Bye", "Falk", 2005)

# Kroeger
map_by_name("Cobra", "Kroeger")

# Parris
map_by_name("springfield", "Parris")

conn.commit()

# Report remaining unmapped
unmapped = conn.execute("""
    SELECT t.season, t.name, t.manager_name
    FROM teams t LEFT JOIN team_owner_map m ON t.team_key=m.team_key
    WHERE m.owner_id IS NULL ORDER BY t.season, t.name
""").fetchall()
print(f"{len(unmapped)} still unmapped:")
for r in unmapped:
    print(f"  {r[0]}  {r[1]:<30}  {r[2]}")

conn.close()
