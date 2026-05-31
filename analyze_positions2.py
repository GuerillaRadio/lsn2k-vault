import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))
from database import get_conn
conn = get_conn()

# First check data coverage per season
print("Data coverage check — champion seasons with starter stats:")
for r in conn.execute("""
    SELECT c.season, o.nickname as champ,
           COUNT(DISTINCT rs.week) as weeks_with_data,
           COUNT(*) as starter_slots,
           SUM(CASE WHEN pws.fantasy_points IS NOT NULL THEN 1 ELSE 0 END) as has_pts
    FROM championships c
    JOIN owners o ON c.owner_id=o.owner_id
    JOIN teams t ON t.season=c.season
    JOIN team_owner_map tom ON t.team_key=tom.team_key AND tom.owner_id=c.owner_id
    JOIN roster_slots rs ON rs.team_key=t.team_key
    JOIN player_weekly_stats pws ON rs.player_key=pws.player_key AND rs.week=pws.week AND rs.league_key=pws.league_key
    WHERE rs.is_starting=1
    GROUP BY c.season, o.owner_id
    ORDER BY c.season
""").fetchall():
    print(f"  {r['season']}: {r['champ']:<10} {r['weeks_with_data']} weeks, {r['starter_slots']} slots, {r['has_pts']} with pts")

conn.close()
