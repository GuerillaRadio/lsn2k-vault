import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))
from database import get_conn
conn = get_conn()

print("Owner all-time: rings / runner-up / playoffs")
for r in conn.execute("""
    SELECT nickname, championships, runner_up, playoff_appearances
    FROM owner_all_time ORDER BY championships DESC, playoff_appearances DESC
""").fetchall():
    print(f"  {r['nickname']}: {r['championships']} rings, {r['runner_up']} runner-up, {r['playoff_appearances']} playoffs")

print("\nAll final-week championship games:")
for r in conn.execute("""
    SELECT m.season, o1.nickname as t1, o2.nickname as t2,
           m.team1_points, m.team2_points,
           ow.nickname as winner
    FROM matchups m
    JOIN team_owner_map map1 ON m.team1_key=map1.team_key
    JOIN owners o1 ON map1.owner_id=o1.owner_id
    JOIN team_owner_map map2 ON m.team2_key=map2.team_key
    JOIN owners o2 ON map2.owner_id=o2.owner_id
    JOIN team_owner_map mapw ON m.winner_team_key=mapw.team_key
    JOIN owners ow ON mapw.owner_id=ow.owner_id
    JOIN leagues l ON m.league_key=l.league_key
    WHERE m.is_playoffs=1 AND m.is_consolation=0 AND m.week=l.end_week
    ORDER BY m.season
""").fetchall():
    print(f"  {r['season']}: {r['t1']} ({r['team1_points']}) vs {r['t2']} ({r['team2_points']}) — {r['winner']} wins")

conn.close()
