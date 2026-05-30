import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))
from database import get_conn

conn = get_conn()

# Add column if it doesn't exist
try:
    conn.execute("ALTER TABLE owners ADD COLUMN franchise_name TEXT")
    conn.commit()
except Exception:
    pass  # column already exists

franchises = [
    ("Falk",    "cockgobblins"),
    ("Garlich", "Chicken Roasters"),
    ("Scott",   "Knoblauch's Fanclub"),
    ("Utz",     "Jobu's Rum"),
    ("Nic",     "STEALTH"),
    ("Carson",  "Space Truckers"),
    ("Chou",    "Asian Tiger"),
    ("Garrett", "Spineless Monkey"),
    ("James",   "Belcher Doubtful"),
    ("Larson",  "The Carpet Cleaners"),
    ("T-Bone",  "Black Dynamite"),
    ("Dusty",   "Bubb Rubb n' Lil Sis"),
]

for nick, fname in franchises:
    conn.execute("UPDATE owners SET franchise_name=? WHERE nickname=?", (fname, nick))

conn.commit()

print("Franchise names set:")
for r in conn.execute("SELECT nickname, full_name, franchise_name FROM owners ORDER BY nickname").fetchall():
    fn = r["franchise_name"] or "(none)"
    print(f"  {r['full_name']} ({r['nickname']}): {fn}")

conn.close()
