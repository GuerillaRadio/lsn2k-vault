import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))
from database import get_conn
conn = get_conn()

print("Fantasy points coverage for starters 2004-2009:")
for r in conn.execute("""
    SELECT pws.season,
           COUNT(*) as total,
           SUM(CASE WHEN pws.fantasy_points IS NOT NULL THEN 1 ELSE 0 END) as has_pts,
           SUM(CASE WHEN pws.fantasy_points IS NULL AND rs.is_starting=1 THEN 1 ELSE 0 END) as starting_no_pts
    FROM player_weekly_stats pws
    JOIN roster_slots rs ON pws.player_key=rs.player_key AND pws.season=rs.season
        AND pws.week=rs.week AND pws.league_key=rs.league_key
    WHERE pws.season BETWEEN 2004 AND 2009
    GROUP BY pws.season ORDER BY pws.season
""").fetchall():
    pct = r['has_pts']/r['total']*100 if r['total'] else 0
    print(f"  {r['season']}: {pct:.0f}% have points, {r['starting_no_pts']} starters w/o pts")

conn.close()
