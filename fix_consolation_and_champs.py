"""
1. Fix championships table with correct data
2. Detect and mark consolation games properly
3. Rebuild aggregates excluding consolation games
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))
from database import get_conn

conn = get_conn()

# ── 1. Fix championships ────────────────────────────────────────────────────
print("Fixing championships table...")

CORRECT_CHAMPS = {
    2004: ["Utz"],
    2005: ["Carson"],
    2006: ["Falk"],
    2007: ["Falk"],
    2008: ["Nic"],
    2009: ["Falk"],
    2010: ["Falk"],
    2011: ["Utz"],
    2012: ["Garrett"],
    2013: ["Nic"],
    2014: ["Chou"],
    2015: ["Falk"],
    2016: ["Scott"],
    2017: ["James"],
    2018: ["Garlich"],
    2019: ["Garlich"],
    2020: ["Garlich"],
    2021: ["T-Bone"],
    2022: ["Scott", "Nic"],  # co-champions
    2023: ["Larson"],
    2024: ["Scott"],
    2025: ["Utz"],
}

def oid(nick):
    row = conn.execute("SELECT owner_id FROM owners WHERE nickname=?", (nick,)).fetchone()
    if not row:
        raise ValueError(f"Owner not found: {nick}")
    return row[0]

conn.execute("DELETE FROM championships")
for season, nicks in CORRECT_CHAMPS.items():
    note = "co-champion (tied 85.5-85.5)" if season == 2022 else None
    for nick in nicks:
        conn.execute("INSERT INTO championships (season, owner_id, note) VALUES (?,?,?)",
                     (season, oid(nick), note))

conn.commit()
print(f"  Inserted {sum(len(v) for v in CORRECT_CHAMPS.values())} championship records.")

# ── 2. Map 2009 teams to owners ─────────────────────────────────────────────
print("\nMapping 2009 teams to owners (by manager_name)...")
name_to_nick = {
    "Utz": "Utz", "Garrett": "Garrett", "Eric Falk": "Falk",
    "Scott": "Scott", "Carson": "Carson", "Matt Larson": "Larson",
    "Nick G": "Nic", "Todd": "Hippe", "Dustin": "Dusty",
    "da": "Chou", "James": "James", "Garlich": "Garlich",
    "Jon": "Parris",
}
teams_2009 = conn.execute(
    "SELECT team_key, name, manager_name FROM teams WHERE season=2009"
).fetchall()
for t in teams_2009:
    nick = name_to_nick.get(t["manager_name"])
    if nick:
        owner_id = oid(nick)
        conn.execute("INSERT OR REPLACE INTO team_owner_map (team_key, owner_id) VALUES (?,?)",
                     (t["team_key"], owner_id))
        print(f"  {t['name']} -> {nick}")
    else:
        print(f"  WARNING: no match for {t['name']} ({t['manager_name']})")
conn.commit()

# ── 3. Detect and mark consolation games ────────────────────────────────────
print("\nDetecting consolation games...")

total_fixed = 0
seasons = conn.execute("SELECT season, league_key, playoff_start_week, num_playoff_teams FROM leagues ORDER BY season").fetchall()

for row in seasons:
    season = row["season"]
    league_key = row["league_key"]
    num_playoff_teams = row["num_playoff_teams"] or 4  # default to 4

    # Get regular season standings to identify playoff teams
    # Playoff teams = those with rank <= num_playoff_teams
    playoff_teams = set(r["team_key"] for r in conn.execute("""
        SELECT team_key, rank FROM standings
        WHERE league_key=? AND rank > 0 AND rank <= ?
    """, (league_key, num_playoff_teams)).fetchall())

    # Get all playoff matchups sorted by week
    matchups = conn.execute("""
        SELECT id, week, team1_key, team2_key, winner_team_key
        FROM matchups
        WHERE league_key=? AND is_playoffs=1
        ORDER BY week
    """, (league_key,)).fetchall()

    if not matchups:
        continue

    # Track which teams have lost a playoff game (they go to consolation)
    eliminated = set()  # teams that lost a real playoff game
    non_playoff = set()  # teams that didn't make the real playoffs

    # Teams not in playoff_teams are non-playoff (all their games are consolation)
    all_teams_in_playoffs = set()
    for m in matchups:
        all_teams_in_playoffs.add(m["team1_key"])
        if m["team2_key"]:
            all_teams_in_playoffs.add(m["team2_key"])

    if playoff_teams:
        non_playoff = all_teams_in_playoffs - playoff_teams
    # If no standings data, can't determine — skip consolation marking

    weeks = sorted(set(m["week"] for m in matchups))
    consolation_ids = set()

    for week in weeks:
        week_matchups = [m for m in matchups if m["week"] == week]
        for m in week_matchups:
            t1, t2 = m["team1_key"], m["team2_key"]
            # Mark as consolation if either team is non-playoff or already eliminated
            if t1 in non_playoff or t2 in non_playoff or \
               t1 in eliminated or t2 in eliminated:
                consolation_ids.add(m["id"])
            else:
                # Real playoff game — loser gets eliminated to consolation
                if m["winner_team_key"] and m["winner_team_key"] != t1:
                    eliminated.add(t1)
                elif m["winner_team_key"] and m["winner_team_key"] != t2:
                    if t2:
                        eliminated.add(t2)

    # Update is_consolation flag
    if consolation_ids:
        conn.executemany("UPDATE matchups SET is_consolation=1 WHERE id=?",
                         [(i,) for i in consolation_ids])
        total_fixed += len(consolation_ids)

    # Count for reporting
    real_playoff = len([m for m in matchups if m["id"] not in consolation_ids])
    print(f"  {season}: {real_playoff} real playoff games, {len(consolation_ids)} marked consolation")

conn.commit()
print(f"  Total consolation games marked: {total_fixed}")

conn.close()

# ── 4. Rebuild aggregates ────────────────────────────────────────────────────
print("\nRebuilding aggregates...")
import subprocess
subprocess.run([sys.executable, "build_aggregates.py"])
