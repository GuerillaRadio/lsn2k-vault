"""
Derive champions by tracing the playoff bracket:
Championship game = final-week game where BOTH teams won their previous playoff game.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))
from database import get_conn

conn = get_conn()

seasons = conn.execute("SELECT season, league_key, end_week FROM leagues ORDER BY season").fetchall()

derived = {}
problems = []

for row in seasons:
    season = row["season"]
    end_week = row["end_week"]
    league_key = row["league_key"]

    # Get all playoff matchups for this season
    playoff_matchups = conn.execute("""
        SELECT week, team1_key, team2_key, winner_team_key, team1_points, team2_points
        FROM matchups
        WHERE league_key=? AND is_playoffs=1 AND is_bye=0 AND winner_team_key IS NOT NULL
        ORDER BY week
    """, (league_key,)).fetchall()

    if not playoff_matchups:
        problems.append(f"{season}: no playoff matchups")
        continue

    # Find playoff weeks
    weeks = sorted(set(m["week"] for m in playoff_matchups))
    if len(weeks) < 2:
        problems.append(f"{season}: only 1 playoff week")
        continue

    final_week = max(weeks)
    semifinal_week = weeks[-2]

    # Winners of the semifinal week
    semifinal_winners = set()
    for m in playoff_matchups:
        if m["week"] == semifinal_week:
            semifinal_winners.add(m["winner_team_key"])

    # Championship game = final-week game where both teams were semifinal winners
    champ_winner = None
    champ_game = None
    for m in playoff_matchups:
        if m["week"] == final_week:
            if m["team1_key"] in semifinal_winners and m["team2_key"] in semifinal_winners:
                champ_winner = m["winner_team_key"]
                champ_game = m
                break

    if not champ_winner:
        # Fallback: highest combined score in final week (most likely championship)
        final_games = [m for m in playoff_matchups if m["week"] == final_week]
        if final_games:
            best = max(final_games, key=lambda m: (m["team1_points"] or 0) + (m["team2_points"] or 0))
            champ_winner = best["winner_team_key"]
            champ_game = best
            problems.append(f"{season}: used score fallback")

    if champ_winner:
        owner = conn.execute("""
            SELECT o.nickname, o.owner_id FROM owners o
            JOIN team_owner_map m ON o.owner_id=m.owner_id
            WHERE m.team_key=?
        """, (champ_winner,)).fetchone()
        if owner:
            derived[season] = {"owner_id": owner["owner_id"], "nickname": owner["nickname"]}
        else:
            problems.append(f"{season}: champion team {champ_winner} has no owner mapping")
    else:
        problems.append(f"{season}: could not determine champion")

print("Derived champions:")
for season in sorted(derived.keys()):
    d = derived[season]
    print(f"  {season}: {d['nickname']}")

if problems:
    print(f"\nProblems ({len(problems)}):")
    for p in problems: print(f"  {p}")

# Check against existing championships table
print("\nComparing to existing championships table:")
existing = {r["season"]: r["nickname"] for r in conn.execute("""
    SELECT c.season, o.nickname FROM championships c JOIN owners o ON c.owner_id=o.owner_id
""").fetchall()}

mismatches = []
for season, d in sorted(derived.items()):
    ex = existing.get(season)
    if ex and ex != d["nickname"]:
        mismatches.append(f"  {season}: derived={d['nickname']}, existing={ex}")
    elif not ex:
        mismatches.append(f"  {season}: MISSING — derived={d['nickname']}")

if mismatches:
    print("  Mismatches/missing:")
    for m in mismatches: print(m)
else:
    print("  All match!")

# Insert missing ones
print("\nInserting missing champions...")
for season, d in sorted(derived.items()):
    if season not in existing:
        conn.execute("INSERT OR IGNORE INTO championships (season, owner_id) VALUES (?,?)",
                     (season, d["owner_id"]))
        print(f"  Added: {season} → {d['nickname']}")

conn.commit()
conn.close()
print("Done.")
