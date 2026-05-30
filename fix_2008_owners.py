import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))
from database import get_conn

conn = get_conn()

def oid(nick):
    return conn.execute("SELECT owner_id FROM owners WHERE nickname=?", (nick,)).fetchone()[0]

# Fix: "Jobus rum" (da) is Chou, not Utz
jobus_lower = conn.execute(
    "SELECT team_key FROM teams WHERE season=2008 AND name='Jobus rum'"
).fetchone()
if jobus_lower:
    conn.execute("INSERT OR REPLACE INTO team_owner_map (team_key, owner_id) VALUES (?,?)",
                 (jobus_lower["team_key"], oid("Chou")))
    print("Fixed: Jobus rum -> Chou")

# Fix: "Put'n the Bunny Down" is Wiley, not Dusty
bunny = conn.execute(
    "SELECT team_key FROM teams WHERE season=2008 AND name LIKE '%Bunny%'"
).fetchone()
if bunny:
    conn.execute("INSERT OR REPLACE INTO team_owner_map (team_key, owner_id) VALUES (?,?)",
                 (bunny["team_key"], oid("Wiley")))
    print("Fixed: Put'n the Bunny Down -> Wiley")

conn.commit()

# Verify
print("\n2008 teams after fix:")
for r in conn.execute("""
    SELECT t.name, o.nickname, t.manager_name
    FROM teams t
    JOIN team_owner_map m ON t.team_key=m.team_key
    JOIN owners o ON m.owner_id=o.owner_id
    WHERE t.season=2008 ORDER BY o.nickname
""").fetchall():
    print(f"  {r['nickname']:>10}  |  {r['name']:<30}  |  {r['manager_name']}")

conn.close()

print("\nRebuilding aggregates...")
import subprocess
subprocess.run([sys.executable, "build_aggregates.py"])
