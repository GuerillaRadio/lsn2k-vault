import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))
from database import get_conn

conn = get_conn()

print("2023 scoring settings:")
rows = conn.execute("""
    SELECT ss.stat_id, sc.name, sc.display_name, ss.value
    FROM scoring_settings ss
    LEFT JOIN stat_categories sc ON ss.stat_id=sc.stat_id AND sc.game_key=(
        SELECT game_key FROM leagues WHERE season=2023
    )
    WHERE ss.league_key=(SELECT league_key FROM leagues WHERE season=2023)
    AND ss.value != 0
    ORDER BY ABS(ss.value) DESC
""").fetchall()
for r in rows:
    print(f"  {str(r['stat_id']):>4}  {str(r['display_name'] or '?'):>8}  {r['value']:>6}  {r['name']}")

print("\nSample team scores from 2023 matchups:")
rows = conn.execute("""
    SELECT week, team1_points, team2_points FROM matchups
    WHERE season=2023 AND is_playoffs=0 AND week<=3
    ORDER BY week, team1_points DESC LIMIT 10
""").fetchall()
for r in rows:
    print(f"  Week {r['week']}: {r['team1_points']} vs {r['team2_points']}")

print("\nChecking playoff game structure - 2023 final week:")
rows = conn.execute("""
    SELECT m.week, m.is_playoffs, m.is_consolation,
           o1.nickname as owner1, o2.nickname as owner2,
           m.team1_points, m.team2_points, m.winner_team_key
    FROM matchups m
    JOIN team_owner_map map1 ON m.team1_key=map1.team_key
    JOIN owners o1 ON map1.owner_id=o1.owner_id
    JOIN team_owner_map map2 ON m.team2_key=map2.team_key
    JOIN owners o2 ON map2.owner_id=o2.owner_id
    WHERE m.season=2023 AND m.is_playoffs=1
    ORDER BY m.week, m.is_consolation, m.team1_points+m.team2_points DESC
""").fetchall()
for r in rows:
    tag = "CONSOLATION" if r["is_consolation"] else "PLAYOFF"
    print(f"  Week {r['week']} [{tag}]: {r['owner1']} vs {r['owner2']} — {r['team1_points']} vs {r['team2_points']}")

conn.close()
