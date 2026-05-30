"""
Build all pre-computed analytics tables.
Run after any data update. All tables are historical and immutable except during season.
"""
import sys, json
from pathlib import Path
from datetime import datetime, timezone
sys.path.insert(0, str(Path(__file__).parent / "src"))
from database import get_conn

conn = get_conn()

def drop_create(sql):
    table = sql.split("TABLE")[1].split("(")[0].strip()
    conn.execute(f"DROP TABLE IF EXISTS {table}")
    conn.executescript(sql)
    conn.commit()

print("Building all analytics tables...\n")

# ═══════════════════════════════════════════════════════════════════════════
# TIER 1 — HIGH FREQUENCY
# ═══════════════════════════════════════════════════════════════════════════

# ── 1. matchup_results ─────────────────────────────────────────────────────
# One row per team per game — makes every record/score query a simple SELECT
print("1. matchup_results...")
drop_create("""
    CREATE TABLE matchup_results (
        id                  INTEGER PRIMARY KEY AUTOINCREMENT,
        matchup_id          INTEGER,
        season              INTEGER,
        week                INTEGER,
        owner_id            INTEGER,
        nickname            TEXT,
        franchise_name      TEXT,
        opponent_id         INTEGER,
        opponent_nickname   TEXT,
        team_points         REAL,
        opponent_points     REAL,
        won                 INTEGER,
        tied                INTEGER,
        lost                INTEGER,
        point_diff          REAL,
        is_playoffs         INTEGER DEFAULT 0,
        is_consolation      INTEGER DEFAULT 0,
        is_regular_season   INTEGER DEFAULT 1
    );
""")

conn.execute("""
    INSERT INTO matchup_results
        (matchup_id, season, week, owner_id, nickname, franchise_name,
         opponent_id, opponent_nickname, team_points, opponent_points,
         won, tied, lost, point_diff, is_playoffs, is_consolation, is_regular_season)
    SELECT
        m.id, m.season, m.week,
        o1.owner_id, o1.nickname, COALESCE(o1.franchise_name, o1.nickname),
        o2.owner_id, o2.nickname,
        CAST(m.team1_points AS REAL), CAST(m.team2_points AS REAL),
        CASE WHEN m.winner_team_key=m.team1_key THEN 1 ELSE 0 END,
        CASE WHEN m.winner_team_key IS NULL AND m.team1_points IS NOT NULL THEN 1 ELSE 0 END,
        CASE WHEN m.winner_team_key=m.team2_key THEN 1 ELSE 0 END,
        CAST(m.team1_points AS REAL) - CAST(m.team2_points AS REAL),
        m.is_playoffs, m.is_consolation,
        CASE WHEN m.is_playoffs=0 THEN 1 ELSE 0 END
    FROM matchups m
    JOIN team_owner_map map1 ON m.team1_key=map1.team_key
    JOIN owners o1 ON map1.owner_id=o1.owner_id
    JOIN team_owner_map map2 ON m.team2_key=map2.team_key
    JOIN owners o2 ON map2.owner_id=o2.owner_id
    WHERE m.team2_key IS NOT NULL AND m.is_bye=0

    UNION ALL

    SELECT
        m.id, m.season, m.week,
        o2.owner_id, o2.nickname, COALESCE(o2.franchise_name, o2.nickname),
        o1.owner_id, o1.nickname,
        CAST(m.team2_points AS REAL), CAST(m.team1_points AS REAL),
        CASE WHEN m.winner_team_key=m.team2_key THEN 1 ELSE 0 END,
        CASE WHEN m.winner_team_key IS NULL AND m.team2_points IS NOT NULL THEN 1 ELSE 0 END,
        CASE WHEN m.winner_team_key=m.team1_key THEN 1 ELSE 0 END,
        CAST(m.team2_points AS REAL) - CAST(m.team1_points AS REAL),
        m.is_playoffs, m.is_consolation,
        CASE WHEN m.is_playoffs=0 THEN 1 ELSE 0 END
    FROM matchups m
    JOIN team_owner_map map1 ON m.team1_key=map1.team_key
    JOIN owners o1 ON map1.owner_id=o1.owner_id
    JOIN team_owner_map map2 ON m.team2_key=map2.team_key
    JOIN owners o2 ON map2.owner_id=o2.owner_id
    WHERE m.team2_key IS NOT NULL AND m.is_bye=0
""")
conn.execute("CREATE INDEX IF NOT EXISTS idx_mr_owner ON matchup_results(owner_id, season)")
conn.execute("CREATE INDEX IF NOT EXISTS idx_mr_season ON matchup_results(season, week)")
conn.commit()
print(f"   {conn.execute('SELECT COUNT(*) FROM matchup_results').fetchone()[0]:,} rows")

# ── 2. owner_playoff_stats ─────────────────────────────────────────────────
print("2. owner_playoff_stats...")
drop_create("""
    CREATE TABLE owner_playoff_stats (
        owner_id                INTEGER PRIMARY KEY,
        nickname                TEXT,
        full_name               TEXT,
        franchise_name          TEXT,
        playoff_appearances     INTEGER DEFAULT 0,
        playoff_wins            INTEGER DEFAULT 0,
        playoff_losses          INTEGER DEFAULT 0,
        championship_appearances INTEGER DEFAULT 0,
        championships           INTEGER DEFAULT 0,
        runner_up               INTEGER DEFAULT 0,
        playoff_win_pct         REAL DEFAULT 0,
        best_playoff_finish     INTEGER,
        avg_playoff_finish      REAL
    );
""")

conn.execute("""
    INSERT INTO owner_playoff_stats
        (owner_id, nickname, full_name, franchise_name,
         playoff_appearances, playoff_wins, playoff_losses,
         championship_appearances, championships, runner_up,
         playoff_win_pct, best_playoff_finish, avg_playoff_finish)
    SELECT
        o.owner_id, o.nickname, o.full_name, COALESCE(o.franchise_name, o.nickname),
        COUNT(DISTINCT CASE WHEN fs.made_playoffs=1 THEN fs.season END),
        SUM(CASE WHEN mr.is_playoffs=1 AND mr.is_consolation=0 AND mr.won=1 THEN 1 ELSE 0 END),
        SUM(CASE WHEN mr.is_playoffs=1 AND mr.is_consolation=0 AND mr.lost=1 THEN 1 ELSE 0 END),
        COUNT(DISTINCT CASE WHEN fs.final_rank<=2 THEN fs.season END),
        COUNT(DISTINCT CASE WHEN fs.final_rank=1 THEN fs.season END),
        COUNT(DISTINCT CASE WHEN fs.final_rank=2 THEN fs.season END),
        CASE WHEN
            SUM(CASE WHEN mr.is_playoffs=1 AND mr.is_consolation=0 THEN 1 ELSE 0 END) > 0
        THEN ROUND(1.0 *
            SUM(CASE WHEN mr.is_playoffs=1 AND mr.is_consolation=0 AND mr.won=1 THEN 1 ELSE 0 END) /
            SUM(CASE WHEN mr.is_playoffs=1 AND mr.is_consolation=0 THEN 1 ELSE 0 END), 3)
        ELSE 0 END,
        MIN(CASE WHEN fs.made_playoffs=1 THEN fs.final_rank END),
        ROUND(AVG(CASE WHEN fs.made_playoffs=1 THEN CAST(fs.final_rank AS REAL) END), 1)
    FROM owners o
    LEFT JOIN matchup_results mr ON o.owner_id=mr.owner_id
    LEFT JOIN owner_season_stats fs ON o.owner_id=fs.owner_id
    GROUP BY o.owner_id
""")
conn.commit()
print(f"   {conn.execute('SELECT COUNT(*) FROM owner_playoff_stats').fetchone()[0]} rows")

# ── 3. waiver_summary ──────────────────────────────────────────────────────
print("3. waiver_summary...")
drop_create("""
    CREATE TABLE waiver_summary (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        transaction_key TEXT,
        season          INTEGER,
        pickup_week     INTEGER,
        pickup_date     TEXT,
        owner_id        INTEGER,
        nickname        TEXT,
        player_key      TEXT,
        player_name     TEXT,
        position        TEXT,
        pts_before      REAL DEFAULT 0,
        pts_after       REAL DEFAULT 0,
        pts_total       REAL DEFAULT 0,
        weeks_rostered  INTEGER DEFAULT 0
    );
""")

league_end_weeks = {r["season"]: r["end_week"] for r in conn.execute("SELECT season, end_week FROM leagues").fetchall()}

adds = conn.execute("""
    SELECT t.transaction_key, t.season, t.league_key, t.timestamp,
           tp.player_key, tp.player_name, tp.dest_team_key,
           p.position, tp.source_type
    FROM transactions t
    JOIN transaction_players tp ON t.transaction_key=tp.transaction_key
    LEFT JOIN players p ON tp.player_key=p.player_key
    WHERE t.type='add' AND t.status='successful'
    AND tp.source_type IN ('waivers','freeagents')
    AND tp.player_key IS NOT NULL AND tp.dest_team_key IS NOT NULL
""").fetchall()

league_map = {}
for r in conn.execute("SELECT league_key, season FROM leagues").fetchall():
    league_map[r["league_key"]] = r["season"]

for a in adds:
    season = a["season"]
    end_week = league_end_weeks.get(season, 17)
    pickup_week, pickup_date = 1, "unknown"
    if a["timestamp"]:
        try:
            dt = datetime.fromtimestamp(int(a["timestamp"]), tz=timezone.utc)
            pickup_date = dt.strftime("%Y-%m-%d")
            season_start = datetime(season, 9, 7, tzinfo=timezone.utc)
            days_in = max(0, (dt - season_start).days)
            pickup_week = min(max(1, days_in // 7 + 1), end_week)
        except Exception:
            pass

    owner = conn.execute("""
        SELECT o.owner_id, o.nickname FROM team_owner_map m JOIN owners o ON m.owner_id=o.owner_id
        WHERE m.team_key=?
    """, (a["dest_team_key"],)).fetchone()
    if not owner:
        continue

    def get_pts(week_start, week_end):
        r = conn.execute("""
            SELECT SUM(CAST(fantasy_points AS REAL)) FROM player_weekly_stats
            WHERE league_key=? AND player_key=? AND season=? AND week>=? AND week<=?
            AND fantasy_points IS NOT NULL
        """, (a["league_key"], a["player_key"], season, week_start, week_end)).fetchone()
        return round(float(r[0] or 0), 2)

    pts_before = get_pts(1, pickup_week)
    pts_after  = get_pts(pickup_week + 1, end_week)
    weeks = conn.execute("""
        SELECT COUNT(DISTINCT week) FROM roster_slots
        WHERE league_key=? AND player_key=? AND season=? AND week>?
    """, (a["league_key"], a["player_key"], season, pickup_week)).fetchone()[0]

    conn.execute("""
        INSERT INTO waiver_summary
            (transaction_key, season, pickup_week, pickup_date, owner_id, nickname,
             player_key, player_name, position, pts_before, pts_after, pts_total, weeks_rostered)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (a["transaction_key"], season, pickup_week, pickup_date,
          owner["owner_id"], owner["nickname"], a["player_key"],
          a["player_name"], a["position"],
          pts_before, pts_after, round(pts_before + pts_after, 2), int(weeks or 0)))

conn.commit()
print(f"   {conn.execute('SELECT COUNT(*) FROM waiver_summary').fetchone()[0]:,} rows")


# ═══════════════════════════════════════════════════════════════════════════
# TIER 2 — STORY DEPTH
# ═══════════════════════════════════════════════════════════════════════════

# ── 4. bench_points ────────────────────────────────────────────────────────
print("4. bench_points...")
drop_create("""
    CREATE TABLE bench_points (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        season          INTEGER,
        week            INTEGER,
        owner_id        INTEGER,
        nickname        TEXT,
        pts_started     REAL DEFAULT 0,
        pts_benched     REAL DEFAULT 0,
        pts_left_on_bench REAL DEFAULT 0,
        UNIQUE(season, week, owner_id)
    );
""")

conn.execute("""
    INSERT OR IGNORE INTO bench_points (season, week, owner_id, nickname, pts_started, pts_benched, pts_left_on_bench)
    SELECT
        rs.season, rs.week,
        o.owner_id, o.nickname,
        ROUND(SUM(CASE WHEN rs.is_starting=1 THEN CAST(pws.fantasy_points AS REAL) ELSE 0 END), 2),
        ROUND(SUM(CASE WHEN rs.is_starting=0 AND rs.selected_position!='IR' THEN CAST(pws.fantasy_points AS REAL) ELSE 0 END), 2),
        ROUND(SUM(CASE WHEN rs.is_starting=0 AND rs.selected_position!='IR' THEN CAST(pws.fantasy_points AS REAL) ELSE 0 END), 2)
    FROM roster_slots rs
    JOIN player_weekly_stats pws ON rs.player_key=pws.player_key AND rs.week=pws.week AND rs.league_key=pws.league_key
    JOIN team_owner_map m ON rs.team_key=m.team_key
    JOIN owners o ON m.owner_id=o.owner_id
    WHERE pws.fantasy_points IS NOT NULL
    GROUP BY rs.season, rs.week, o.owner_id
""")
conn.execute("CREATE INDEX IF NOT EXISTS idx_bp_owner ON bench_points(owner_id, season)")
conn.commit()
print(f"   {conn.execute('SELECT COUNT(*) FROM bench_points').fetchone()[0]:,} rows")

# ── 5. draft_pick_value ────────────────────────────────────────────────────
print("5. draft_pick_value...")
drop_create("""
    CREATE TABLE draft_pick_value (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        season          INTEGER,
        round           INTEGER,
        pick            INTEGER,
        overall_pick    INTEGER,
        owner_id        INTEGER,
        nickname        TEXT,
        player_key      TEXT,
        player_name     TEXT,
        position        TEXT,
        season_pts      REAL DEFAULT 0,
        avg_pts_at_pick REAL DEFAULT 0,
        value_over_avg  REAL DEFAULT 0,
        was_starter     INTEGER DEFAULT 0
    );
""")

draft_picks = conn.execute("""
    SELECT dp.season, dp.round, dp.pick, dp.team_key, dp.player_key,
           p.name as player_name, p.position,
           o.owner_id, o.nickname, l.league_key, l.num_teams
    FROM draft_picks dp
    JOIN leagues l ON dp.league_key=l.league_key
    LEFT JOIN players p ON dp.player_key=p.player_key
    JOIN team_owner_map m ON dp.team_key=m.team_key
    JOIN owners o ON m.owner_id=o.owner_id
    WHERE dp.player_key IS NOT NULL
""").fetchall()

# Pre-compute season totals per player per league
for dp in draft_picks:
    overall = (dp["round"] - 1) * dp["num_teams"] + dp["pick"]
    pts_row = conn.execute("""
        SELECT SUM(CAST(fantasy_points AS REAL)) FROM player_weekly_stats
        WHERE league_key=? AND player_key=? AND season=? AND fantasy_points IS NOT NULL
    """, (dp["league_key"], dp["player_key"], dp["season"])).fetchone()
    season_pts = round(float(pts_row[0] or 0), 2)

    starter_weeks = conn.execute("""
        SELECT COUNT(*) FROM roster_slots
        WHERE league_key=? AND player_key=? AND season=? AND is_starting=1
    """, (dp["league_key"], dp["player_key"], dp["season"])).fetchone()[0]

    conn.execute("""
        INSERT INTO draft_pick_value
            (season, round, pick, overall_pick, owner_id, nickname,
             player_key, player_name, position, season_pts, was_starter)
        VALUES (?,?,?,?,?,?,?,?,?,?,?)
    """, (dp["season"], dp["round"], dp["pick"], overall,
          dp["owner_id"], dp["nickname"], dp["player_key"],
          dp["player_name"], dp["position"], season_pts,
          1 if starter_weeks > 0 else 0))

conn.commit()

# Update avg_pts_at_pick and value_over_avg
conn.execute("""
    UPDATE draft_pick_value SET
        avg_pts_at_pick = (
            SELECT ROUND(AVG(d2.season_pts), 2) FROM draft_pick_value d2
            WHERE d2.overall_pick BETWEEN draft_pick_value.overall_pick-2
            AND draft_pick_value.overall_pick+2
        )
""")
conn.execute("""
    UPDATE draft_pick_value SET
        value_over_avg = ROUND(season_pts - avg_pts_at_pick, 2)
    WHERE avg_pts_at_pick IS NOT NULL
""")
conn.execute("CREATE INDEX IF NOT EXISTS idx_dpv_owner ON draft_pick_value(owner_id, season)")
conn.commit()
print(f"   {conn.execute('SELECT COUNT(*) FROM draft_pick_value').fetchone()[0]:,} rows")

# ── 6. owner_streaks ───────────────────────────────────────────────────────
print("6. owner_streaks...")
drop_create("""
    CREATE TABLE owner_streaks (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        owner_id        INTEGER,
        nickname        TEXT,
        streak_type     TEXT,
        length          INTEGER,
        start_season    INTEGER,
        start_week      INTEGER,
        end_season      INTEGER,
        end_week        INTEGER,
        is_current      INTEGER DEFAULT 0
    );
""")

owners = conn.execute("SELECT owner_id, nickname FROM owners").fetchall()
for owner in owners:
    oid = owner["owner_id"]
    games = conn.execute("""
        SELECT season, week, won, lost
        FROM matchup_results
        WHERE owner_id=? AND is_regular_season=1 AND is_consolation=0
        AND team_points IS NOT NULL
        ORDER BY season, week
    """, (oid,)).fetchall()

    if not games:
        continue

    streaks = []
    cur_type, cur_len = None, 0
    cur_start = None

    for i, g in enumerate(games):
        result = 'W' if g["won"] else ('L' if g["lost"] else None)
        if result is None:
            continue
        if result == cur_type:
            cur_len += 1
        else:
            if cur_type and cur_len >= 3:
                streaks.append((cur_type, cur_len, cur_start, games[i-1]))
            cur_type = result
            cur_len = 1
            cur_start = g

    if cur_type and cur_len >= 3:
        streaks.append((cur_type, cur_len, cur_start, games[-1]))

    is_current_type = cur_type
    is_current_len  = cur_len

    for stype, slen, sstart, send in streaks:
        is_cur = 1 if (stype == is_current_type and send == games[-1]) else 0
        conn.execute("""
            INSERT INTO owner_streaks
                (owner_id, nickname, streak_type, length, start_season, start_week,
                 end_season, end_week, is_current)
            VALUES (?,?,?,?,?,?,?,?,?)
        """, (oid, owner["nickname"], 'win' if stype=='W' else 'loss',
              slen, sstart["season"], sstart["week"],
              send["season"], send["week"], is_cur))

conn.commit()
print(f"   {conn.execute('SELECT COUNT(*) FROM owner_streaks').fetchone()[0]} rows")


# ═══════════════════════════════════════════════════════════════════════════
# TIER 3 — AWARDS & STORIES
# ═══════════════════════════════════════════════════════════════════════════

# ── 7. season_awards ───────────────────────────────────────────────────────
print("7. season_awards...")
drop_create("""
    CREATE TABLE season_awards (
        season                  INTEGER PRIMARY KEY,
        most_pts_owner          TEXT,
        most_pts_value          REAL,
        least_pts_owner         TEXT,
        least_pts_value         REAL,
        best_record_owner       TEXT,
        best_record_wins        INTEGER,
        worst_record_owner      TEXT,
        worst_record_wins       INTEGER,
        highest_week_owner      TEXT,
        highest_week_score      REAL,
        highest_week_week       INTEGER,
        lowest_week_owner       TEXT,
        lowest_week_score       REAL,
        biggest_blowout_winner  TEXT,
        biggest_blowout_margin  REAL,
        closest_game_margin     REAL,
        most_bench_pts_owner    TEXT,
        most_bench_pts_total    REAL,
        most_trades_owner       TEXT,
        most_trades_count       INTEGER,
        champion                TEXT,
        runner_up               TEXT
    );
""")

seasons = [r["season"] for r in conn.execute("SELECT season FROM leagues WHERE is_finished=1 ORDER BY season").fetchall()]
for s in seasons:
    def sc(sql, *args):
        r = conn.execute(sql, args or (s,)).fetchone()
        return r if r else (None, None)

    mp = sc("SELECT nickname, ROUND(SUM(team_points),2) FROM matchup_results WHERE season=? AND is_regular_season=1 AND is_consolation=0 GROUP BY owner_id ORDER BY 2 DESC LIMIT 1")
    lp = sc("SELECT nickname, ROUND(SUM(team_points),2) FROM matchup_results WHERE season=? AND is_regular_season=1 AND is_consolation=0 GROUP BY owner_id ORDER BY 2 ASC LIMIT 1")
    br = sc("SELECT nickname, SUM(won) as w FROM matchup_results WHERE season=? AND is_regular_season=1 AND is_consolation=0 GROUP BY owner_id ORDER BY w DESC LIMIT 1")
    wr = sc("SELECT nickname, SUM(won) as w FROM matchup_results WHERE season=? AND is_regular_season=1 AND is_consolation=0 GROUP BY owner_id ORDER BY w ASC LIMIT 1")
    hw = sc("SELECT nickname, MAX(team_points), week FROM matchup_results WHERE season=? AND is_consolation=0 AND team_points IS NOT NULL ORDER BY team_points DESC LIMIT 1")
    lw = sc("SELECT nickname, MIN(team_points) FROM matchup_results WHERE season=? AND is_regular_season=1 AND team_points IS NOT NULL ORDER BY team_points ASC LIMIT 1")
    bb = sc("SELECT nickname, MAX(ABS(point_diff)) FROM matchup_results WHERE season=? AND is_regular_season=1 AND won=1 ORDER BY ABS(point_diff) DESC LIMIT 1")
    cg = sc("SELECT MIN(ABS(point_diff)) FROM matchup_results WHERE season=? AND is_regular_season=1 AND team_points IS NOT NULL AND ABS(point_diff) > 0 LIMIT 1", s)
    mb = sc("SELECT nickname, ROUND(SUM(pts_left_on_bench),2) FROM bench_points WHERE season=? GROUP BY owner_id ORDER BY 2 DESC LIMIT 1")
    mt = sc("SELECT trader_nickname, COUNT(*) as n FROM trade_summary WHERE season=? GROUP BY trader_nickname ORDER BY n DESC LIMIT 1")
    ch = sc("SELECT o.nickname FROM championships c JOIN owners o ON c.owner_id=o.owner_id WHERE c.season=? AND (c.note IS NULL OR c.note NOT LIKE '%runner%') LIMIT 1")
    ru = sc("SELECT nickname FROM final_standings fs JOIN owners o ON fs.owner_id=o.owner_id WHERE fs.season=? AND fs.final_rank=2 LIMIT 1")

    conn.execute("""
        INSERT OR REPLACE INTO season_awards VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (s,
          mp[0], mp[1] if len(mp)>1 else None,
          lp[0], lp[1] if len(lp)>1 else None,
          br[0], br[1] if len(br)>1 else None,
          wr[0], wr[1] if len(wr)>1 else None,
          hw[0], hw[1] if len(hw)>2 else hw[1] if len(hw)>1 else None,
          hw[2] if len(hw)>2 else None,
          lw[0], lw[1] if len(lw)>1 else None,
          bb[0], bb[1] if len(bb)>1 else None,
          cg[0] if cg else None,
          mb[0], mb[1] if len(mb)>1 else None,
          mt[0], mt[1] if len(mt)>1 else None,
          ch[0], ru[0]))

conn.commit()
print(f"   {conn.execute('SELECT COUNT(*) FROM season_awards').fetchone()[0]} rows")

# ── 8. owner_vs_owner ──────────────────────────────────────────────────────
# Full season-by-season breakdown for every head-to-head pairing
print("8. owner_vs_owner (season breakdowns)...")
drop_create("""
    CREATE TABLE owner_vs_owner (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        owner_id        INTEGER,
        opponent_id     INTEGER,
        season          INTEGER,
        wins            INTEGER DEFAULT 0,
        losses          INTEGER DEFAULT 0,
        ties            INTEGER DEFAULT 0,
        pts_for         REAL DEFAULT 0,
        pts_against     REAL DEFAULT 0,
        UNIQUE(owner_id, opponent_id, season)
    );
""")

conn.execute("""
    INSERT OR IGNORE INTO owner_vs_owner (owner_id, opponent_id, season, wins, losses, ties, pts_for, pts_against)
    SELECT
        owner_id, opponent_id, season,
        SUM(won), SUM(lost), SUM(tied),
        ROUND(SUM(team_points), 2), ROUND(SUM(opponent_points), 2)
    FROM matchup_results
    WHERE is_regular_season=1 AND is_consolation=0 AND team_points IS NOT NULL
    GROUP BY owner_id, opponent_id, season
""")
conn.execute("CREATE INDEX IF NOT EXISTS idx_ovo ON owner_vs_owner(owner_id, opponent_id)")
conn.commit()
print(f"   {conn.execute('SELECT COUNT(*) FROM owner_vs_owner').fetchone()[0]:,} rows")

# ── Summary ────────────────────────────────────────────────────────────────
print("\nAll analytics tables built:")
for t in ['matchup_results','owner_playoff_stats','waiver_summary',
          'bench_points','draft_pick_value','owner_streaks',
          'season_awards','owner_vs_owner']:
    n = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
    print(f"  {t}: {n:,} rows")

conn.close()
print("\nDone.")
