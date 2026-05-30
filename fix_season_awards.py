import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))
from database import get_conn
conn = get_conn()

conn.execute("DROP TABLE IF EXISTS season_awards")
conn.executescript("""
    CREATE TABLE season_awards (
        season INTEGER PRIMARY KEY,
        most_pts_owner TEXT, most_pts_value REAL,
        least_pts_owner TEXT, least_pts_value REAL,
        best_record_owner TEXT, best_record_wins INTEGER,
        worst_record_owner TEXT, worst_record_wins INTEGER,
        highest_week_owner TEXT, highest_week_score REAL, highest_week_week INTEGER,
        lowest_week_owner TEXT, lowest_week_score REAL,
        biggest_blowout_winner TEXT, biggest_blowout_margin REAL,
        closest_game_margin REAL,
        most_bench_pts_owner TEXT, most_bench_pts_total REAL,
        most_trades_owner TEXT, most_trades_count INTEGER,
        champion TEXT, runner_up TEXT
    );
""")
conn.commit()

def val(row, i, default=None):
    try:
        return row[i] if row and row[i] is not None else default
    except Exception:
        return default

seasons = [r["season"] for r in conn.execute("SELECT season FROM leagues WHERE is_finished=1 ORDER BY season").fetchall()]

for s in seasons:
    def q(sql):
        return conn.execute(sql, (s,)).fetchone()

    mp = q("SELECT nickname, ROUND(SUM(team_points),2) FROM matchup_results WHERE season=? AND is_regular_season=1 AND is_consolation=0 GROUP BY owner_id ORDER BY 2 DESC LIMIT 1")
    lp = q("SELECT nickname, ROUND(SUM(team_points),2) FROM matchup_results WHERE season=? AND is_regular_season=1 AND is_consolation=0 GROUP BY owner_id ORDER BY 2 ASC LIMIT 1")
    br = q("SELECT nickname, SUM(won) FROM matchup_results WHERE season=? AND is_regular_season=1 AND is_consolation=0 GROUP BY owner_id ORDER BY 2 DESC LIMIT 1")
    wr = q("SELECT nickname, SUM(won) FROM matchup_results WHERE season=? AND is_regular_season=1 AND is_consolation=0 GROUP BY owner_id ORDER BY 2 ASC LIMIT 1")
    hw = q("SELECT nickname, team_points, week FROM matchup_results WHERE season=? AND is_consolation=0 AND team_points IS NOT NULL ORDER BY team_points DESC LIMIT 1")
    lw = q("SELECT nickname, team_points FROM matchup_results WHERE season=? AND is_regular_season=1 AND team_points IS NOT NULL ORDER BY team_points ASC LIMIT 1")
    bb = q("SELECT nickname, ABS(point_diff) FROM matchup_results WHERE season=? AND is_regular_season=1 AND won=1 ORDER BY ABS(point_diff) DESC LIMIT 1")
    cg = q("SELECT MIN(ABS(point_diff)) FROM matchup_results WHERE season=? AND is_regular_season=1 AND team_points IS NOT NULL AND ABS(point_diff) > 0")
    mb = q("SELECT nickname, ROUND(SUM(pts_left_on_bench),2) FROM bench_points WHERE season=? GROUP BY owner_id ORDER BY 2 DESC LIMIT 1")
    mt = q("SELECT trader_nickname, COUNT(*) FROM trade_summary WHERE season=? GROUP BY trader_nickname ORDER BY 2 DESC LIMIT 1")
    ch = q("SELECT o.nickname FROM championships c JOIN owners o ON c.owner_id=o.owner_id WHERE c.season=? LIMIT 1")
    ru = q("SELECT o.nickname FROM final_standings fs JOIN owners o ON fs.owner_id=o.owner_id WHERE fs.season=? AND fs.final_rank=2 LIMIT 1")

    conn.execute("INSERT OR REPLACE INTO season_awards VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (
        s,
        val(mp,0), val(mp,1),
        val(lp,0), val(lp,1),
        val(br,0), val(br,1),
        val(wr,0), val(wr,1),
        val(hw,0), val(hw,1), val(hw,2),
        val(lw,0), val(lw,1),
        val(bb,0), val(bb,1),
        val(cg,0),
        val(mb,0), val(mb,1),
        val(mt,0), val(mt,1),
        val(ch,0), val(ru,0)
    ))

conn.commit()
n = conn.execute("SELECT COUNT(*) FROM season_awards").fetchone()[0]
print(f"season_awards: {n} rows")

# Also build owner_vs_owner
conn.execute("DROP TABLE IF EXISTS owner_vs_owner")
conn.executescript("""
    CREATE TABLE owner_vs_owner (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        owner_id INTEGER, opponent_id INTEGER, season INTEGER,
        wins INTEGER DEFAULT 0, losses INTEGER DEFAULT 0, ties INTEGER DEFAULT 0,
        pts_for REAL DEFAULT 0, pts_against REAL DEFAULT 0,
        UNIQUE(owner_id, opponent_id, season)
    );
""")
conn.execute("""
    INSERT OR IGNORE INTO owner_vs_owner (owner_id, opponent_id, season, wins, losses, ties, pts_for, pts_against)
    SELECT owner_id, opponent_id, season,
           SUM(won), SUM(lost), SUM(tied),
           ROUND(SUM(team_points),2), ROUND(SUM(opponent_points),2)
    FROM matchup_results
    WHERE is_regular_season=1 AND is_consolation=0 AND team_points IS NOT NULL
    GROUP BY owner_id, opponent_id, season
""")
conn.execute("CREATE INDEX IF NOT EXISTS idx_ovo ON owner_vs_owner(owner_id, opponent_id)")
conn.commit()
n2 = conn.execute("SELECT COUNT(*) FROM owner_vs_owner").fetchone()[0]
print(f"owner_vs_owner: {n2:,} rows")

# Quick sanity check on season_awards
print("\nSample 2023 awards:")
r = conn.execute("SELECT * FROM season_awards WHERE season=2023").fetchone()
if r:
    print(f"  Most pts: {r['most_pts_owner']} ({r['most_pts_value']})")
    print(f"  Highest week: {r['highest_week_owner']} wk{r['highest_week_week']} ({r['highest_week_score']})")
    print(f"  Champion: {r['champion']}, Runner-up: {r['runner_up']}")

conn.close()
print("\nAll 8 tables complete.")
