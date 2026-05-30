import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))
from database import get_conn

conn = get_conn()
chou = conn.execute("SELECT owner_id FROM owners WHERE nickname=?", ("Chou",)).fetchone()[0]

rows = conn.execute(
    "SELECT team_key, name FROM teams WHERE name LIKE ? OR name LIKE ?",
    ("%croat%", "%Croatian%")
).fetchall()

for r in rows:
    conn.execute("INSERT OR REPLACE INTO team_owner_map (team_key,owner_id) VALUES (?,?)", (r[0], chou))
    print(f"Fixed: {r[1]}")

conn.commit()

total = conn.execute("SELECT COUNT(*) FROM team_owner_map").fetchone()[0]
total_teams = conn.execute("SELECT COUNT(*) FROM teams").fetchone()[0]
print(f"Mapped: {total}/{total_teams}")
conn.close()
