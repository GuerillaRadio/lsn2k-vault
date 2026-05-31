"""
Pre-compute player_season_stats — one row per player per season.
Regular season = is_playoffs=0, is_consolation=0.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))
from database import get_conn

conn = get_conn()

conn.execute("DROP TABLE IF EXISTS player_season_stats")
conn.executescript("""
    CREATE TABLE player_season_stats (
        id                  INTEGER PRIMARY KEY AUTOINCREMENT,
        player_key          TEXT NOT NULL,
        player_name         TEXT,
        position            TEXT,
        nfl_team            TEXT,
        season              INTEGER NOT NULL,
        league_key          TEXT NOT NULL,
        reg_season_pts      REAL DEFAULT 0,
        playoff_pts         REAL DEFAULT 0,
        total_pts           REAL DEFAULT 0,
        weeks_started       INTEGER DEFAULT 0,
        weeks_benched       INTEGER DEFAULT 0,
        best_week_pts       REAL,
        best_week           INTEGER,
        worst_week_pts      REAL,
        UNIQUE(player_key, season, league_key)
    );
""")
conn.commit()

print("Building player_season_stats...")

conn.execute("""
    INSERT OR IGNORE INTO player_season_stats
        (player_key, player_name, position, nfl_team, season, league_key,
         reg_season_pts, playoff_pts, total_pts,
         weeks_started, weeks_benched, best_week_pts, best_week, worst_week_pts)
    SELECT
        pws.player_key,
        p.name,
        p.position,
        p.nfl_team,
        pws.season,
        pws.league_key,
        ROUND(SUM(CASE WHEN m.is_playoffs=0 AND m.is_consolation=0
                  THEN CAST(pws.fantasy_points AS REAL) ELSE 0 END), 2),
        ROUND(SUM(CASE WHEN m.is_playoffs=1 AND m.is_consolation=0
                  THEN CAST(pws.fantasy_points AS REAL) ELSE 0 END), 2),
        ROUND(SUM(CAST(pws.fantasy_points AS REAL)), 2),
        SUM(CASE WHEN rs.is_starting=1 THEN 1 ELSE 0 END),
        SUM(CASE WHEN rs.is_starting=0 AND rs.selected_position!='IR' THEN 1 ELSE 0 END),
        MAX(CAST(pws.fantasy_points AS REAL)),
        (SELECT week FROM player_weekly_stats p2
         WHERE p2.player_key=pws.player_key AND p2.season=pws.season AND p2.league_key=pws.league_key
         ORDER BY CAST(p2.fantasy_points AS REAL) DESC LIMIT 1),
        MIN(CASE WHEN rs.is_starting=1 THEN CAST(pws.fantasy_points AS REAL) END)
    FROM player_weekly_stats pws
    JOIN roster_slots rs ON pws.player_key=rs.player_key AND pws.week=rs.week AND pws.league_key=rs.league_key
    JOIN matchups m ON rs.team_key=m.team1_key AND pws.week=m.week AND pws.league_key=m.league_key
    LEFT JOIN players p ON pws.player_key=p.player_key
    WHERE pws.fantasy_points IS NOT NULL
    GROUP BY pws.player_key, pws.season, pws.league_key
""")
conn.commit()

n = conn.execute("SELECT COUNT(*) FROM player_season_stats").fetchone()[0]
print(f"Built {n:,} player-season records.")

print("\nSample — top QBs by regular season points 2023:")
for r in conn.execute("""
    SELECT player_name, position, reg_season_pts, weeks_started, best_week_pts
    FROM player_season_stats
    WHERE season=2023 AND position='QB' AND weeks_started >= 8
    ORDER BY reg_season_pts DESC LIMIT 5
""").fetchall():
    print(f"  {r['player_name']}: {r['reg_season_pts']} pts ({r['weeks_started']} starts, best week: {r['best_week_pts']})")

conn.execute("CREATE INDEX IF NOT EXISTS idx_pss_position ON player_season_stats(position, season)")
conn.execute("CREATE INDEX IF NOT EXISTS idx_pss_player ON player_season_stats(player_key, season)")
conn.commit()
conn.close()
print("\nDone.")
