import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))
from database import get_conn
conn = get_conn()

print("Carson's championships:")
for r in conn.execute("""
    SELECT c.season, c.note FROM championships c
    JOIN owners o ON c.owner_id=o.owner_id
    WHERE o.nickname='Carson'
""").fetchall():
    print(f"  {r['season']}: {r['note'] or 'champion'}")

print("\nCarson's playoff appearances by season:")
for r in conn.execute("""
    SELECT oss.season, oss.made_playoffs, oss.won_championship
    FROM owner_season_stats oss
    JOIN owners o ON oss.owner_id=o.owner_id
    WHERE o.nickname='Carson' AND oss.made_playoffs=1
    ORDER BY oss.season
""").fetchall():
    champ = " (CHAMPION)" if r['won_championship'] else ""
    print(f"  {r['season']}{champ}")

print("\nFinal week playoff games involving Carson:")
for r in conn.execute("""
    SELECT m.season, m.week, o1.nickname as t1, o2.nickname as t2,
           m.team1_points, m.team2_points, m.winner_team_key,
           m.is_playoffs, m.is_consolation
    FROM matchups m
    JOIN team_owner_map map1 ON m.team1_key=map1.team_key
    JOIN owners o1 ON map1.owner_id=o1.owner_id
    JOIN team_owner_map map2 ON m.team2_key=map2.team_key
    JOIN owners o2 ON map2.owner_id=o2.owner_id
    JOIN leagues l ON m.league_key=l.league_key
    WHERE (o1.nickname='Carson' OR o2.nickname='Carson')
      AND m.is_playoffs=1 AND m.is_consolation=0
      AND m.week=l.end_week
    ORDER BY m.season
""").fetchall():
    winner_map1 = r['winner_team_key'] and r['t1'] == 'Carson'
    result = "WON" if winner_map1 else ("LOST" if r['winner_team_key'] else "TIE")
    print(f"  {r['season']} wk{r['week']}: Carson vs {r['t2']} — {r['team1_points']} vs {r['team2_points']} [{result}]")

conn.close()
