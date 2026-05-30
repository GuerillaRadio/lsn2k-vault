import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))
from database import get_conn
conn = get_conn()
issues = []

def flag(msg):
    issues.append(msg)
    print(f"  *** {msg}")

print("=== 1. DUPLICATE MATCHUPS ===")
dups = conn.execute("""
    SELECT league_key, week, team1_key, COUNT(*) as n
    FROM matchups GROUP BY league_key, week, team1_key HAVING n > 1
""").fetchall()
print(f"  {len(dups)} duplicate matchup records")
if dups:
    for d in dups[:5]: print(f"    {d['league_key']} week {d['week']} {d['team1_key']}")
    flag(f"{len(dups)} duplicate matchups found")

print("\n=== 2. MATCHUP WINNER CONSISTENCY ===")
bad = conn.execute("""
    SELECT COUNT(*) FROM matchups
    WHERE winner_team_key IS NOT NULL
    AND winner_team_key != team1_key
    AND winner_team_key != team2_key
    AND is_bye = 0
""").fetchone()[0]
print(f"  {bad} matchups where winner isn't team1 or team2")
if bad: flag(f"{bad} matchups with invalid winner_team_key")

print("\n=== 3. PLAYOFF FLAGS ===")
for r in conn.execute("""
    SELECT season,
           SUM(CASE WHEN is_playoffs=1 AND is_consolation=0 THEN 1 ELSE 0 END) as real_playoff,
           SUM(CASE WHEN is_consolation=1 THEN 1 ELSE 0 END) as consolation
    FROM matchups GROUP BY season ORDER BY season
""").fetchall():
    if r['real_playoff'] == 0 and r['season'] != 2026:
        print(f"  {r['season']}: {r['real_playoff']} real playoff, {r['consolation']} consolation  <-- NO REAL PLAYOFFS")
        flag(f"{r['season']}: no real playoff games flagged")
    else:
        print(f"  {r['season']}: {r['real_playoff']} real playoff, {r['consolation']} consolation")

print("\n=== 4. DRAFT PICKS - MISSING PLAYER NAMES ===")
missing_names = conn.execute("""
    SELECT COUNT(*) FROM draft_picks dp
    LEFT JOIN players p ON dp.player_key = p.player_key
    WHERE dp.player_key IS NOT NULL AND p.player_key IS NULL
""").fetchone()[0]
print(f"  {missing_names} draft picks with no player name in players table")
if missing_names > 0: flag(f"{missing_names} draft picks reference unknown players")

print("\n=== 5. OWNER SEASON STATS vs STANDINGS CONSISTENCY ===")
mismatches = conn.execute("""
    SELECT oss.season, o.nickname, oss.wins as oss_wins, s.wins as std_wins,
           oss.losses as oss_losses, s.losses as std_losses
    FROM owner_season_stats oss
    JOIN owners o ON oss.owner_id=o.owner_id
    JOIN teams t ON t.season=oss.season
    JOIN team_owner_map m ON t.team_key=m.team_key AND m.owner_id=oss.owner_id
    JOIN standings s ON s.team_key=t.team_key
    WHERE s.wins > 0 AND ABS(oss.wins - s.wins) > 2
    LIMIT 10
""").fetchall()
print(f"  {len(mismatches)} significant mismatches between computed and Yahoo standings")
for r in mismatches:
    print(f"    {r['season']} {r['nickname']}: computed={r['oss_wins']}W, yahoo={r['std_wins']}W")
    flag(f"{r['season']} {r['nickname']}: wins mismatch computed={r['oss_wins']} vs yahoo={r['std_wins']}")

print("\n=== 6. H2H SELF-MATCHUPS ===")
self_play = conn.execute("SELECT COUNT(*) FROM owner_h2h WHERE owner1_id=owner2_id").fetchone()[0]
print(f"  {self_play} self-matchup records (should be 0)")
if self_play: flag(f"{self_play} self-matchup records in owner_h2h")

print("\n=== 7. SEASONS MISSING FROM AGGREGATES ===")
seasons_in_db = set(r[0] for r in conn.execute("SELECT DISTINCT season FROM leagues").fetchall())
seasons_in_agg = set(r[0] for r in conn.execute("SELECT DISTINCT season FROM owner_season_stats").fetchall())
missing_agg = seasons_in_db - seasons_in_agg
if missing_agg:
    print(f"  Missing from aggregates: {missing_agg}")
    flag(f"Seasons missing from owner_season_stats: {missing_agg}")
else:
    print("  All seasons represented in aggregates")

print("\n=== 8. FANTASY POINTS COVERAGE ===")
for r in conn.execute("""
    SELECT pws.season,
           COUNT(*) as total,
           SUM(CASE WHEN pws.fantasy_points IS NOT NULL THEN 1 ELSE 0 END) as has_pts,
           SUM(CASE WHEN pws.fantasy_points IS NULL AND rs.is_starting=1 THEN 1 ELSE 0 END) as starting_no_pts
    FROM player_weekly_stats pws
    JOIN roster_slots rs ON pws.player_key=rs.player_key AND pws.season=rs.season AND pws.week=rs.week AND pws.league_key=rs.league_key
    WHERE pws.season BETWEEN 2010 AND 2025
    GROUP BY pws.season ORDER BY pws.season
""").fetchall():
    pct = r['has_pts']/r['total']*100 if r['total'] else 0
    flag_str = f"  <-- {r['starting_no_pts']} STARTERS missing pts" if r['starting_no_pts'] > 20 else ""
    print(f"  {r['season']}: {pct:.0f}% have points, {r['starting_no_pts']} starters w/o pts{flag_str}")
    if r['starting_no_pts'] > 50:
        flag(f"{r['season']}: {r['starting_no_pts']} starters missing fantasy points")

print("\n=== 9. TRANSACTION COMPLETENESS ===")
for r in conn.execute("SELECT season, COUNT(*) as n FROM transactions GROUP BY season ORDER BY season").fetchall():
    if r['n'] == 0:
        flag(f"{r['season']}: zero transactions")

print("\n=== 10. RESPONSE CACHE - STALE ENTRIES ===")
cache_count = conn.execute("SELECT COUNT(*) FROM response_cache").fetchone()[0]
print(f"  {cache_count} cached responses")
if cache_count > 0:
    print("  Recommend clearing cache since data has changed significantly")
    flag("Response cache has entries — may be stale after data fixes")

print("\n=== 11. CHAMPIONSHIPS vs SEASONS ===")
for r in conn.execute("""
    SELECT l.season FROM leagues l
    LEFT JOIN championships c ON l.season=c.season
    WHERE c.season IS NULL AND l.season != 2026
    ORDER BY l.season
""").fetchall():
    print(f"  {r['season']}: NO CHAMPION RECORDED")
    flag(f"{r['season']}: missing champion")

print(f"\n{'='*50}")
print(f"TOTAL ISSUES: {len(issues)}")
for i in issues:
    print(f"  - {i}")

conn.close()
