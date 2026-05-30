"""Audit which query types are still complex vs already pre-computed."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))
from database import get_conn
conn = get_conn()

# Check what tables already exist
tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()]
print("Existing tables:")
for t in tables:
    n = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
    print(f"  {t}: {n:,} rows")

print("\nSample complex queries that currently require multiple joins:")

# 1. Playoff record per owner (requires joining matchups + 2x team_owner_map + filter)
print("\n1. Playoff record (non-consolation only):")
for r in conn.execute("""
    SELECT o.nickname,
           SUM(CASE WHEN m.winner_team_key=map.team_key THEN 1 ELSE 0 END) as pw,
           SUM(CASE WHEN m.winner_team_key!=map.team_key AND m.winner_team_key IS NOT NULL THEN 1 ELSE 0 END) as pl
    FROM matchups m
    JOIN team_owner_map map ON (m.team1_key=map.team_key OR m.team2_key=map.team_key)
    JOIN owners o ON map.owner_id=o.owner_id
    WHERE m.is_playoffs=1 AND m.is_consolation=0
    GROUP BY o.owner_id ORDER BY pw DESC LIMIT 5
""").fetchall():
    print(f"  {r['nickname']}: {r['pw']}W-{r['pl']}L in playoffs")

# 2. Bench points left per season (starter vs bench comparison)
print("\n2. Bench points sample (2023 wk1):")
for r in conn.execute("""
    SELECT o.nickname,
           SUM(CASE WHEN rs.is_starting=1 THEN CAST(pws.fantasy_points AS REAL) ELSE 0 END) as started,
           SUM(CASE WHEN rs.is_starting=0 AND rs.selected_position!='IR' THEN CAST(pws.fantasy_points AS REAL) ELSE 0 END) as benched
    FROM roster_slots rs
    JOIN player_weekly_stats pws ON rs.player_key=pws.player_key AND rs.week=pws.week AND rs.league_key=pws.league_key
    JOIN team_owner_map m ON rs.team_key=m.team_key
    JOIN owners o ON m.owner_id=o.owner_id
    WHERE rs.season=2023 AND rs.week=1 AND rs.league_key='423.l.7779'
    GROUP BY o.owner_id ORDER BY benched DESC LIMIT 3
""").fetchall():
    print(f"  {r['nickname']}: started {r['started']:.1f}, benched {r['benched']:.1f}")

# 3. Waiver pickups that scored big that season
print("\n3. Best waiver pickups sample:")
for r in conn.execute("""
    SELECT tp.player_name, t.season, o.nickname,
           SUM(CAST(pws.fantasy_points AS REAL)) as pts_after
    FROM transactions t
    JOIN transaction_players tp ON t.transaction_key=tp.transaction_key
    JOIN team_owner_map m ON tp.dest_team_key=m.team_key
    JOIN owners o ON m.owner_id=o.owner_id
    JOIN player_weekly_stats pws ON tp.player_key=pws.player_key AND t.season=pws.season
    WHERE t.type='add' AND tp.source_type='waivers' AND pws.fantasy_points IS NOT NULL
    GROUP BY t.transaction_key, tp.player_key
    ORDER BY pts_after DESC LIMIT 5
""").fetchall():
    print(f"  {r['player_name']} ({r['season']}) picked up by {r['nickname']}: {r['pts_after']:.1f} pts after")

conn.close()
