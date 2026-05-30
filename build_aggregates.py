"""
Build pre-computed aggregate tables from matchup data.
Run this after any backfill or data update.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))
from database import get_conn

conn = get_conn()

conn.executescript("""
    -- ── Response cache ────────────────────────────────────────────────────
    CREATE TABLE IF NOT EXISTS response_cache (
        question_hash   TEXT PRIMARY KEY,
        question        TEXT NOT NULL,
        answer          TEXT NOT NULL,
        created_at      INTEGER DEFAULT (strftime('%s','now')),
        hit_count       INTEGER DEFAULT 0
    );

    -- ── Owner season stats (computed from matchups) ───────────────────────
    DROP TABLE IF EXISTS owner_season_stats;
    CREATE TABLE owner_season_stats (
        owner_id            INTEGER NOT NULL REFERENCES owners(owner_id),
        season              INTEGER NOT NULL,
        team_name           TEXT,
        franchise_name      TEXT,
        wins                INTEGER DEFAULT 0,
        losses              INTEGER DEFAULT 0,
        ties                INTEGER DEFAULT 0,
        points_for          REAL DEFAULT 0,
        points_against      REAL DEFAULT 0,
        playoff_seed        INTEGER,
        made_playoffs       INTEGER DEFAULT 0,
        final_rank          INTEGER,
        won_championship    INTEGER DEFAULT 0,
        PRIMARY KEY (owner_id, season)
    );

    -- ── Owner all-time stats ──────────────────────────────────────────────
    DROP TABLE IF EXISTS owner_all_time;
    CREATE TABLE owner_all_time (
        owner_id            INTEGER PRIMARY KEY REFERENCES owners(owner_id),
        nickname            TEXT,
        full_name           TEXT,
        franchise_name      TEXT,
        seasons_played      INTEGER DEFAULT 0,
        total_wins          INTEGER DEFAULT 0,
        total_losses        INTEGER DEFAULT 0,
        total_ties          INTEGER DEFAULT 0,
        total_points_for    REAL DEFAULT 0,
        total_points_against REAL DEFAULT 0,
        win_pct             REAL DEFAULT 0,
        playoff_appearances INTEGER DEFAULT 0,
        championships       INTEGER DEFAULT 0,
        runner_up           INTEGER DEFAULT 0,
        best_season_wins    INTEGER DEFAULT 0,
        best_season_year    INTEGER,
        highest_score       REAL DEFAULT 0,
        highest_score_week  INTEGER,
        highest_score_year  INTEGER
    );

    -- ── Head-to-head records ──────────────────────────────────────────────
    DROP TABLE IF EXISTS owner_h2h;
    CREATE TABLE owner_h2h (
        owner1_id           INTEGER NOT NULL REFERENCES owners(owner_id),
        owner2_id           INTEGER NOT NULL REFERENCES owners(owner_id),
        wins                INTEGER DEFAULT 0,
        losses              INTEGER DEFAULT 0,
        ties                INTEGER DEFAULT 0,
        points_for          REAL DEFAULT 0,
        points_against      REAL DEFAULT 0,
        PRIMARY KEY (owner1_id, owner2_id)
    );

    -- ── Weekly high scores ────────────────────────────────────────────────
    DROP TABLE IF EXISTS weekly_high_scores;
    CREATE TABLE weekly_high_scores (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        season      INTEGER,
        week        INTEGER,
        owner_id    INTEGER REFERENCES owners(owner_id),
        team_key    TEXT,
        score       REAL,
        is_playoffs INTEGER DEFAULT 0
    );
""")
conn.commit()
print("Tables created.")

# ── Populate owner_season_stats from matchups ──────────────────────────────
print("Computing season stats from matchups...")

# Get all matchups with owner info
matchups = conn.execute("""
    SELECT
        m.season, m.week, m.is_playoffs, m.is_bye,
        m.team1_key, m.team2_key,
        m.team1_points, m.team2_points,
        m.winner_team_key,
        o1.owner_id as owner1_id,
        o2.owner_id as owner2_id
    FROM matchups m
    JOIN team_owner_map map1 ON m.team1_key = map1.team_key
    JOIN owners o1 ON map1.owner_id = o1.owner_id
    LEFT JOIN team_owner_map map2 ON m.team2_key = map2.team_key
    LEFT JOIN owners o2 ON map2.owner_id = o2.owner_id
    WHERE m.is_bye = 0 AND m.team2_key IS NOT NULL
""").fetchall()

# Accumulate per-owner per-season stats (regular season only)
from collections import defaultdict
stats = defaultdict(lambda: {
    'wins': 0, 'losses': 0, 'ties': 0,
    'points_for': 0.0, 'points_against': 0.0
})

for m in matchups:
    if m['is_playoffs']:
        continue
    s = m['season']
    o1, o2 = m['owner1_id'], m['owner2_id']
    p1, p2 = m['team1_points'] or 0, m['team2_points'] or 0
    wk = m['winner_team_key']

    stats[(o1, s)]['points_for'] += p1
    stats[(o1, s)]['points_against'] += p2
    stats[(o2, s)]['points_for'] += p2
    stats[(o2, s)]['points_against'] += p1

    if wk == m['team1_key']:
        stats[(o1, s)]['wins'] += 1
        stats[(o2, s)]['losses'] += 1
    elif wk == m['team2_key']:
        stats[(o2, s)]['wins'] += 1
        stats[(o1, s)]['losses'] += 1
    else:
        stats[(o1, s)]['ties'] += 1
        stats[(o2, s)]['ties'] += 1

# Insert season stats
for (owner_id, season), s in stats.items():
    team = conn.execute("""
        SELECT t.name, o.franchise_name
        FROM teams t
        JOIN team_owner_map m ON t.team_key=m.team_key
        JOIN owners o ON m.owner_id=o.owner_id
        WHERE m.owner_id=? AND t.season=?
    """, (owner_id, season)).fetchone()

    conn.execute("""
        INSERT OR REPLACE INTO owner_season_stats
            (owner_id, season, team_name, franchise_name, wins, losses, ties, points_for, points_against)
        VALUES (?,?,?,?,?,?,?,?,?)
    """, (
        owner_id, season,
        team['name'] if team else None,
        team['franchise_name'] if team else None,
        s['wins'], s['losses'], s['ties'],
        round(s['points_for'], 2), round(s['points_against'], 2)
    ))

conn.commit()

# Mark playoff appearances and championships
for row in conn.execute("SELECT season, owner_id FROM championships"):
    conn.execute("""
        UPDATE owner_season_stats SET won_championship=1
        WHERE season=? AND owner_id=?
    """, (row['season'], row['owner_id']))

# Derive playoff appearances from matchup data
playoff_owners = conn.execute("""
    SELECT DISTINCT m.season, map1.owner_id
    FROM matchups m
    JOIN team_owner_map map1 ON m.team1_key=map1.team_key
    WHERE m.is_playoffs=1 AND m.is_consolation=0
    UNION
    SELECT DISTINCT m.season, map2.owner_id
    FROM matchups m
    JOIN team_owner_map map2 ON m.team2_key=map2.team_key
    WHERE m.is_playoffs=1 AND m.is_consolation=0
""").fetchall()

for row in playoff_owners:
    conn.execute("""
        INSERT OR IGNORE INTO owner_season_stats (owner_id, season, made_playoffs)
        VALUES (?,?,1)
        ON CONFLICT(owner_id,season) DO UPDATE SET made_playoffs=1
    """, (row['owner_id'], row['season']))

conn.commit()
print(f"  {len(stats)} owner-seasons computed.")

# ── Head-to-head ───────────────────────────────────────────────────────────
print("Computing head-to-head records...")
h2h = defaultdict(lambda: {'wins': 0, 'losses': 0, 'ties': 0, 'pf': 0.0, 'pa': 0.0})

for m in matchups:
    o1, o2 = m['owner1_id'], m['owner2_id']
    p1, p2 = m['team1_points'] or 0, m['team2_points'] or 0
    wk = m['winner_team_key']

    h2h[(o1, o2)]['pf'] += p1
    h2h[(o1, o2)]['pa'] += p2
    h2h[(o2, o1)]['pf'] += p2
    h2h[(o2, o1)]['pa'] += p1

    if wk == m['team1_key']:
        h2h[(o1, o2)]['wins'] += 1
        h2h[(o2, o1)]['losses'] += 1
    elif wk == m['team2_key']:
        h2h[(o2, o1)]['wins'] += 1
        h2h[(o1, o2)]['losses'] += 1
    else:
        h2h[(o1, o2)]['ties'] += 1
        h2h[(o2, o1)]['ties'] += 1

for (o1, o2), d in h2h.items():
    conn.execute("""
        INSERT OR REPLACE INTO owner_h2h
            (owner1_id, owner2_id, wins, losses, ties, points_for, points_against)
        VALUES (?,?,?,?,?,?,?)
    """, (o1, o2, d['wins'], d['losses'], d['ties'], round(d['pf'],2), round(d['pa'],2)))

conn.commit()
print(f"  {len(h2h)} head-to-head pairs computed.")

# ── Weekly high scores ─────────────────────────────────────────────────────
print("Computing weekly high scores...")
for m in matchups:
    for team_key, score, owner_id in [
        (m['team1_key'], m['team1_points'], m['owner1_id']),
        (m['team2_key'], m['team2_points'], m['owner2_id']),
    ]:
        if score:
            conn.execute("""
                INSERT INTO weekly_high_scores
                    (season, week, owner_id, team_key, score, is_playoffs)
                VALUES (?,?,?,?,?,?)
            """, (m['season'], m['week'], owner_id, team_key, score, m['is_playoffs']))

conn.commit()

# ── Owner all-time stats ───────────────────────────────────────────────────
print("Computing all-time stats...")
owners = conn.execute("SELECT owner_id, nickname, full_name, franchise_name FROM owners").fetchall()

for o in owners:
    oid = o['owner_id']
    season_rows = conn.execute("""
        SELECT * FROM owner_season_stats WHERE owner_id=?
    """, (oid,)).fetchall()

    if not season_rows:
        continue

    total_w = sum(r['wins'] for r in season_rows)
    total_l = sum(r['losses'] for r in season_rows)
    total_t = sum(r['ties'] for r in season_rows)
    total_pf = sum(r['points_for'] for r in season_rows)
    total_pa = sum(r['points_against'] for r in season_rows)
    games = total_w + total_l + total_t
    win_pct = round(total_w / games, 3) if games else 0
    playoff_apps = sum(r['made_playoffs'] for r in season_rows)
    championships = sum(r['won_championship'] for r in season_rows)

    # Runner-up: lost the championship game
    runner_up = conn.execute("""
        SELECT COUNT(*) FROM matchups m
        JOIN leagues l ON m.league_key=l.league_key
        JOIN team_owner_map map1 ON m.team1_key=map1.team_key
        JOIN team_owner_map map2 ON m.team2_key=map2.team_key
        WHERE m.is_playoffs=1 AND m.is_consolation=0
          AND m.week=l.end_week
          AND m.winner_team_key IS NOT NULL
          AND (map1.owner_id=? OR map2.owner_id=?)
          AND map1.owner_id!=? OR map2.owner_id!=?
    """, (oid, oid, oid, oid)).fetchone()[0]
    # Simpler: runner-up = appeared in final AND didn't win
    champ_seasons = {r['season'] for r in season_rows if r['won_championship']}
    final_seasons = conn.execute("""
        SELECT DISTINCT m.season FROM matchups m
        JOIN leagues l ON m.league_key=l.league_key
        JOIN team_owner_map tm ON (m.team1_key=tm.team_key OR m.team2_key=tm.team_key)
        WHERE tm.owner_id=? AND m.is_playoffs=1 AND m.is_consolation=0
          AND m.week=l.end_week
    """, (oid,)).fetchall()
    runner_up = sum(1 for r in final_seasons if r['season'] not in champ_seasons)

    best = max(season_rows, key=lambda r: r['wins'])
    high = conn.execute("""
        SELECT season, week, score FROM weekly_high_scores
        WHERE owner_id=? ORDER BY score DESC LIMIT 1
    """, (oid,)).fetchone()

    conn.execute("""
        INSERT OR REPLACE INTO owner_all_time VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        oid, o['nickname'], o['full_name'], o['franchise_name'],
        len(season_rows), total_w, total_l, total_t,
        round(total_pf, 2), round(total_pa, 2), win_pct,
        playoff_apps, championships, runner_up,
        best['wins'], best['season'],
        high['score'] if high else None,
        high['week'] if high else None,
        high['season'] if high else None,
    ))

conn.commit()
print(f"  {len(owners)} owners computed.")

# ── Summary ────────────────────────────────────────────────────────────────
print("\nAll-time standings:")
for r in conn.execute("""
    SELECT full_name, seasons_played, total_wins, total_losses, win_pct,
           championships, playoff_appearances
    FROM owner_all_time ORDER BY championships DESC, win_pct DESC
""").fetchall():
    print(f"  {r['full_name']}: {r['total_wins']}-{r['total_losses']} ({r['win_pct']:.1%}) "
          f"| {r['championships']} rings | {r['playoff_appearances']} playoffs")

conn.close()
print("\nDone.")
