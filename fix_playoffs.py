"""Re-run consolation detection with correct standings data, then rebuild aggregates."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))
from database import get_conn

conn = get_conn()

# Reset all consolation flags first
conn.execute("UPDATE matchups SET is_consolation=0 WHERE is_playoffs=1")
conn.commit()
print("Reset all consolation flags.")

total_fixed = 0
seasons = conn.execute("SELECT season, league_key, num_playoff_teams FROM leagues ORDER BY season").fetchall()

for row in seasons:
    season = row["season"]
    league_key = row["league_key"]
    num_playoff_teams = row["num_playoff_teams"] or 4

    # Get playoff teams from standings (now properly populated)
    playoff_teams = set(r["team_key"] for r in conn.execute("""
        SELECT team_key FROM standings
        WHERE league_key=? AND rank > 0 AND rank <= ?
    """, (league_key, num_playoff_teams)).fetchall())

    matchups = conn.execute("""
        SELECT id, week, team1_key, team2_key, winner_team_key
        FROM matchups WHERE league_key=? AND is_playoffs=1
        ORDER BY week
    """, (league_key,)).fetchall()

    if not matchups:
        continue

    # Teams in playoff matchups that didn't make the real playoffs
    all_in_playoffs = set()
    for m in matchups:
        all_in_playoffs.add(m["team1_key"])
        if m["team2_key"]:
            all_in_playoffs.add(m["team2_key"])

    non_playoff = all_in_playoffs - playoff_teams if playoff_teams else set()
    eliminated = set()
    consolation_ids = set()

    for week in sorted(set(m["week"] for m in matchups)):
        for m in [x for x in matchups if x["week"] == week]:
            t1, t2 = m["team1_key"], m["team2_key"]
            if t1 in non_playoff or (t2 and t2 in non_playoff) or \
               t1 in eliminated or (t2 and t2 in eliminated):
                consolation_ids.add(m["id"])
            else:
                # Real bracket game — loser gets eliminated
                if m["winner_team_key"] and m["winner_team_key"] != t1:
                    eliminated.add(t1)
                elif m["winner_team_key"] and m["winner_team_key"] != t2 and t2:
                    eliminated.add(t2)

    if consolation_ids:
        conn.executemany("UPDATE matchups SET is_consolation=1 WHERE id=?",
                         [(i,) for i in consolation_ids])
        total_fixed += len(consolation_ids)

    real = len([m for m in matchups if m["id"] not in consolation_ids])
    print(f"  {season}: {real} real playoff, {len(consolation_ids)} consolation (num_playoff_teams={num_playoff_teams})")

conn.commit()
print(f"\nTotal consolation games marked: {total_fixed}")
conn.close()

print("\nRebuilding aggregates...")
import subprocess
subprocess.run([sys.executable, "build_aggregates.py"])
