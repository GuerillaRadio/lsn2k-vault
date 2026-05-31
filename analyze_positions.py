import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))
from database import get_conn
conn = get_conn()

print("=== POSITION ANALYSIS: What wins championships? ===\n")

print("1. Average points by position — Champions vs Non-Champions (regular season starters):")
results = conn.execute("""
    SELECT
        p.position,
        ROUND(AVG(CASE WHEN c.owner_id IS NOT NULL THEN CAST(pws.fantasy_points AS REAL) END), 2) as champ_avg,
        ROUND(AVG(CASE WHEN c.owner_id IS NULL THEN CAST(pws.fantasy_points AS REAL) END), 2) as non_champ_avg,
        COUNT(DISTINCT CASE WHEN c.owner_id IS NOT NULL THEN rs.league_key||rs.season END) as champ_seasons
    FROM roster_slots rs
    JOIN player_weekly_stats pws ON rs.player_key=pws.player_key AND rs.week=pws.week AND rs.league_key=pws.league_key
    JOIN players p ON rs.player_key=p.player_key
    JOIN matchups m ON rs.team_key=m.team1_key AND rs.week=m.week AND rs.league_key=m.league_key AND m.is_playoffs=0
    JOIN team_owner_map tom ON rs.team_key=tom.team_key
    LEFT JOIN championships c ON tom.owner_id=c.owner_id AND rs.season=c.season
    WHERE rs.is_starting=1 AND pws.fantasy_points IS NOT NULL
    AND p.position IN ('QB','RB','WR','TE','K','DEF','FLEX')
    GROUP BY p.position ORDER BY champ_avg DESC
""").fetchall()

for r in results:
    diff = round(float(r['champ_avg'] or 0) - float(r['non_champ_avg'] or 0), 2)
    edge = f"+{diff}" if diff > 0 else str(diff)
    print(f"  {r['position']:<6} champ: {r['champ_avg']:>6}  non-champ: {r['non_champ_avg']:>6}  edge: {edge:>6}")

print("\n2. Total season points contribution by position for champions (% of total):")
totals = conn.execute("""
    SELECT p.position,
           ROUND(SUM(CAST(pws.fantasy_points AS REAL)), 1) as total_pts,
           COUNT(*) as starter_weeks
    FROM roster_slots rs
    JOIN player_weekly_stats pws ON rs.player_key=pws.player_key AND rs.week=pws.week AND rs.league_key=pws.league_key
    JOIN players p ON rs.player_key=p.player_key
    JOIN team_owner_map tom ON rs.team_key=tom.team_key
    JOIN championships c ON tom.owner_id=c.owner_id AND rs.season=c.season
    WHERE rs.is_starting=1 AND pws.fantasy_points IS NOT NULL
    AND p.position IN ('QB','RB','WR','TE','K','DEF','FLEX','RB/WR/TE')
    GROUP BY p.position ORDER BY total_pts DESC
""").fetchall()

grand = sum(float(r['total_pts'] or 0) for r in totals)
for r in totals:
    pct = round(float(r['total_pts'] or 0) / grand * 100, 1) if grand else 0
    print(f"  {r['position']:<10} {r['total_pts']:>8,.1f} pts  ({pct}%)")

print("\n3. How many championships were won by the team with the top-scoring QB that season?")
qb_champ = conn.execute("""
    SELECT COUNT(*) as total,
           SUM(CASE WHEN top_qb.owner_id = c.owner_id THEN 1 ELSE 0 END) as qb_won
    FROM championships c
    JOIN (
        SELECT rs.season, tom.owner_id,
               RANK() OVER (PARTITION BY rs.season ORDER BY SUM(CAST(pws.fantasy_points AS REAL)) DESC) as rnk
        FROM roster_slots rs
        JOIN player_weekly_stats pws ON rs.player_key=pws.player_key AND rs.week=pws.week AND rs.league_key=pws.league_key
        JOIN players p ON rs.player_key=p.player_key
        JOIN team_owner_map tom ON rs.team_key=tom.team_key
        JOIN matchups m ON rs.team_key=m.team1_key AND rs.week=m.week AND rs.league_key=m.league_key AND m.is_playoffs=0
        WHERE rs.is_starting=1 AND p.position='QB' AND pws.fantasy_points IS NOT NULL
        GROUP BY rs.season, tom.owner_id
    ) top_qb ON top_qb.season=c.season AND top_qb.rnk=1
    """).fetchone()
print(f"  Top QB scorer won the title: {qb_champ['qb_won']}/{qb_champ['total']} seasons ({round(qb_champ['qb_won']/qb_champ['total']*100)}%)")

print("\n4. Same analysis for RB and WR:")
for pos in ['RB', 'WR']:
    r = conn.execute(f"""
        SELECT COUNT(*) as total,
               SUM(CASE WHEN top_pos.owner_id = c.owner_id THEN 1 ELSE 0 END) as pos_won
        FROM championships c
        JOIN (
            SELECT rs.season, tom.owner_id,
                   RANK() OVER (PARTITION BY rs.season ORDER BY SUM(CAST(pws.fantasy_points AS REAL)) DESC) as rnk
            FROM roster_slots rs
            JOIN player_weekly_stats pws ON rs.player_key=pws.player_key AND rs.week=pws.week AND rs.league_key=pws.league_key
            JOIN players p ON rs.player_key=p.player_key
            JOIN team_owner_map tom ON rs.team_key=tom.team_key
            JOIN matchups m ON rs.team_key=m.team1_key AND rs.week=m.week AND rs.league_key=m.league_key AND m.is_playoffs=0
            WHERE rs.is_starting=1 AND p.position='{pos}' AND pws.fantasy_points IS NOT NULL
            GROUP BY rs.season, tom.owner_id
        ) top_pos ON top_pos.season=c.season AND top_pos.rnk=1
    """).fetchone()
    if r['total']:
        print(f"  Top {pos} scorer won the title: {r['pos_won']}/{r['total']} seasons ({round(r['pos_won']/r['total']*100)}%)")

conn.close()
