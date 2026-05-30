"""Create owners table and map teams to owners."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))
from database import get_conn

conn = get_conn()

conn.executescript("""
    CREATE TABLE IF NOT EXISTS owners (
        owner_id    INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name   TEXT NOT NULL,
        nickname    TEXT,
        yahoo_names TEXT   -- comma-separated Yahoo manager_name values for this person
    );

    CREATE TABLE IF NOT EXISTS team_owner_map (
        team_key    TEXT PRIMARY KEY REFERENCES teams(team_key),
        owner_id    INTEGER REFERENCES owners(owner_id)
    );
""")
conn.commit()

# ── Insert owners ──────────────────────────────────────────────────────────
owners = [
    # (full_name, nickname, yahoo_names)
    ("Clint Utz",          "Utz",     "Utz"),
    ("Garrett Wright",     "Garrett", "Garrett"),
    ("Eric Falk",          "Falk",    "Eric Falk"),
    ("Scott Butler",       "Scott",   "Scott"),
    ("Carson Graff",       "Carson",  "Carson"),
    ("Matt Larson",        "Larson",  "Matt Larson"),
    ("Nick Gililland",     "Nic",     "Nick G"),
    ("Todd Hippe",         "Hippe",   "Todd"),
    ("Dustin Butler",      "Dusty",   "Dustin"),
    ("David Chou",         "Chou",    "da"),
    ("James Andrisevic",   "James",   "James"),
    ("Travis Brown",       "T-Bone",  "Travis"),
    ("Andy Garlich",       "Garlich", "Garlich"),
    ("Brian Hartley",      "Hartley", None),
    ("Nick Wiley",         "Wiley",   None),
]

conn.executemany(
    "INSERT OR IGNORE INTO owners (full_name, nickname, yahoo_names) VALUES (?,?,?)",
    owners
)
conn.commit()

# Helper: get owner_id by nickname
def oid(nickname):
    row = conn.execute("SELECT owner_id FROM owners WHERE nickname=?", (nickname,)).fetchone()
    if not row:
        raise ValueError(f"Owner not found: {nickname}")
    return row[0]

# Helper: map all teams matching a name pattern + optional season filter to an owner
def map_teams(name_pattern, owner_nick, season=None):
    sql = "SELECT team_key FROM teams WHERE name LIKE ?"
    params = [f"%{name_pattern}%"]
    if season:
        sql += " AND season=?"
        params.append(season)
    rows = conn.execute(sql, params).fetchall()
    owner = oid(owner_nick)
    for r in rows:
        conn.execute(
            "INSERT OR REPLACE INTO team_owner_map (team_key, owner_id) VALUES (?,?)",
            (r[0], owner)
        )
    return len(rows)

# ── Map teams by recurring team name patterns ──────────────────────────────
mappings = [
    # (name_pattern, owner_nickname)
    # Clint Utz
    ("Jobu",              "Utz"),
    ("Jobus",             "Utz"),

    # Garrett Wright
    ("Spineless Monkey",  "Garrett"),

    # Eric Falk
    ("cockgobblins",      "Falk"),

    # Scott Butler
    ("Knoblauch",         "Scott"),

    # Carson Graff
    ("Space Truckers",    "Carson"),
    ("Hughsiers",         "Carson"),

    # Matt Larson
    ("Carpet Cleaners",   "Larson"),
    ("Ye Says",           "Larson"),    # 2008

    # Nick Gililland
    ("STEALTH",           "Nic"),
    ("THE STEALTH",       "Nic"),

    # Todd Hippe
    ("Purple Jesus",      "Hippe"),
    ("PurpleJesus",       "Hippe"),
    ("MeepingWith",       "Hippe"),
    ("Black Unicorn",     "Hippe"),
    ("Hingle",            "Hippe"),
    ("Sankey",            "Hippe"),
    ("Turnover Chain",    "Hippe"),

    # Dustin Butler
    ("Bubb Rub",          "Dusty"),
    ("C.Watts",           "Dusty"),
    ("C. Watts",          "Dusty"),
    ("$120",              "Dusty"),
    ("Put'n the Bunny",   "Dusty"),

    # David Chou
    ("Asian Tiger",       "Chou"),
    ("David Chou",        "Chou"),

    # James Andrisevic
    ("Belcher",           "James"),
    ("McNair",            "James"),
    ("Seau",              "James"),
    ("croatian",          "James"),
    ("croat",             "James"),

    # Travis Brown
    ("Black Dynamite",    "T-Bone"),

    # Andy Garlich
    ("Chicken Roast",     "Garlich"),
    ("The Roasters",      "Garlich"),
    ("Roasters Revenge",  "Garlich"),

    # Brian Hartley
    ("Rocky Mountain",    "Hartley"),

    # Nick Wiley
    ("Sharpees",          "Wiley"),
    ("Trivette",          "Wiley"),
]

for pattern, nick in mappings:
    n = map_teams(pattern, nick)
    if n:
        print(f"  {nick}: {n} teams matched '{pattern}'")

# ── Season-specific overrides ──────────────────────────────────────────────
season_maps = [
    # 2004
    ("Untamed Retribution", "Hippe",   2004),
    ("Untamed Retribution", "Hippe",   2005),

    # 2006 one-offs
    ("Super Adventure Club","Hippe",   2006),   # Todd 2006
    ("Lick My Love Pump",   "Dusty",   2006),   # Dustin 2006

    # 2008
    ("Ye Says",             "Larson",  2008),

    # 2011
    ("Shake N Bake",        "James",   2011),   # placeholder - update after 2007 confirm
]

for pattern, nick, season in season_maps:
    n = map_teams(pattern, nick, season)
    if n:
        print(f"  {nick} ({season}): {n} teams matched '{pattern}'")

conn.commit()

# ── Report unmapped teams ──────────────────────────────────────────────────
unmapped = conn.execute("""
    SELECT t.season, t.name, t.manager_name, t.team_key
    FROM teams t
    LEFT JOIN team_owner_map m ON t.team_key = m.team_key
    WHERE m.owner_id IS NULL
    ORDER BY t.season, t.name
""").fetchall()

if unmapped:
    print(f"\n⚠️  {len(unmapped)} teams still unmapped:")
    for r in unmapped:
        print(f"  {r[0]}  {r[1]:<30}  {r[2]}")
else:
    print("\n✅ All teams mapped!")

conn.close()
