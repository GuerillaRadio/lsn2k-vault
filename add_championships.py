"""
Create a championships table with full manual control.
Derives winners from matchup data, then applies custom overrides.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))
from database import get_conn

conn = get_conn()

conn.executescript("""
    CREATE TABLE IF NOT EXISTS championships (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        season      INTEGER NOT NULL,
        owner_id    INTEGER NOT NULL REFERENCES owners(owner_id),
        note        TEXT,   -- e.g. "co-champion", "vacated", etc.
        UNIQUE(season, owner_id)
    );
""")
conn.commit()

def oid(nick):
    row = conn.execute("SELECT owner_id FROM owners WHERE nickname=?", (nick,)).fetchone()
    if not row:
        raise ValueError(f"Owner not found: {nick}")
    return row[0]

# Derive champions from matchup data (final week playoff game, non-consolation)
seasons = conn.execute("SELECT season, end_week FROM leagues ORDER BY season").fetchall()

derived = []
for season, end_week in seasons:
    # Find the championship game: last week, playoffs, not consolation
    champ = conn.execute("""
        SELECT m.winner_team_key, o.owner_id, o.nickname
        FROM matchups m
        JOIN team_owner_map map1 ON m.team1_key = map1.team_key
        JOIN owners o1 ON map1.owner_id = o1.owner_id
        JOIN team_owner_map map2 ON m.team2_key = map2.team_key
        JOIN owners o2 ON map2.owner_id = o2.owner_id
        JOIN team_owner_map mw ON m.winner_team_key = mw.team_key
        JOIN owners o ON mw.owner_id = o.owner_id
        WHERE m.season=? AND m.is_playoffs=1 AND m.is_consolation=0
          AND m.week=? AND m.winner_team_key IS NOT NULL
        LIMIT 1
    """, (season, end_week)).fetchone()

    if champ:
        derived.append((season, champ["owner_id"], champ["nickname"], None))

print("Derived champions:")
for s, oid_, nick, note in derived:
    print(f"  {s}: {nick}")

# Insert derived champions
conn.executemany(
    "INSERT OR IGNORE INTO championships (season, owner_id, note) VALUES (?,?,?)",
    [(s, o, n) for s, o, _, n in derived]
)
conn.commit()

# ── Custom overrides ──────────────────────────────────────────────────────

# 2022: exact tie (85.5-85.5) — both Scott AND Nic get credit
conn.execute("UPDATE championships SET note='co-champion (tied 85.5-85.5)' WHERE season=2022")
conn.execute(
    "INSERT OR IGNORE INTO championships (season, owner_id, note) VALUES (?,?,?)",
    (2022, oid("Nic"), "co-champion (tied 85.5-85.5)")
)
conn.commit()

# ── Report ────────────────────────────────────────────────────────────────
print("\nFinal championship record:")
rows = conn.execute("""
    SELECT c.season, o.nickname, o.full_name, c.note
    FROM championships c JOIN owners o ON c.owner_id=o.owner_id
    ORDER BY c.season, o.nickname
""").fetchall()
for r in rows:
    note = f" ({r['note']})" if r['note'] else ""
    print(f"  {r['season']}: {r['full_name']} ({r['nickname']}){note}")

conn.close()
