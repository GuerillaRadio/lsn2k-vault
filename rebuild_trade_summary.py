"""
1. Deduplicate transaction_players and add UNIQUE constraint
2. Rebuild trade_summary with points_before and points_after for each player
"""
import sys, json
from pathlib import Path
from datetime import datetime, timezone
sys.path.insert(0, str(Path(__file__).parent / "src"))
from database import get_conn

conn = get_conn()

# ── 1. Deduplicate transaction_players ─────────────────────────────────────
print("Deduplicating transaction_players...")
before = conn.execute("SELECT COUNT(*) FROM transaction_players").fetchone()[0]

conn.executescript("""
    CREATE TABLE transaction_players_clean AS
    SELECT MIN(id) as id, transaction_key, player_key, player_name,
           position, nfl_team, transaction_type,
           source_team_key, dest_team_key, source_type, dest_type
    FROM transaction_players
    GROUP BY transaction_key, player_key, COALESCE(dest_team_key,''), transaction_type;

    DROP TABLE transaction_players;

    CREATE TABLE transaction_players (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        transaction_key TEXT NOT NULL REFERENCES transactions(transaction_key),
        player_key      TEXT NOT NULL,
        player_name     TEXT,
        position        TEXT,
        nfl_team        TEXT,
        transaction_type TEXT,
        source_team_key TEXT,
        dest_team_key   TEXT,
        source_type     TEXT,
        dest_type       TEXT,
        UNIQUE(transaction_key, player_key, dest_team_key)
    );

    INSERT INTO transaction_players
        (id, transaction_key, player_key, player_name, position, nfl_team,
         transaction_type, source_team_key, dest_team_key, source_type, dest_type)
    SELECT id, transaction_key, player_key, player_name, position, nfl_team,
           transaction_type, source_team_key, dest_team_key, source_type, dest_type
    FROM transaction_players_clean;

    DROP TABLE transaction_players_clean;

    CREATE INDEX IF NOT EXISTS idx_txp_tx     ON transaction_players(transaction_key);
    CREATE INDEX IF NOT EXISTS idx_txp_player ON transaction_players(player_key);
""")
conn.commit()
after = conn.execute("SELECT COUNT(*) FROM transaction_players").fetchone()[0]
print(f"  Before: {before:,}  After: {after:,}  Removed: {before-after:,} dupes")

# ── 2. Rebuild trade_summary with before/after points ──────────────────────
print("\nRebuilding trade_summary with before/after points...")
conn.execute("DROP TABLE IF EXISTS trade_summary")
conn.executescript("""
    CREATE TABLE trade_summary (
        transaction_key     TEXT PRIMARY KEY,
        season              INTEGER,
        trade_date          TEXT,
        trade_week          INTEGER,
        trader_owner_id     INTEGER,
        tradee_owner_id     INTEGER,
        trader_nickname     TEXT,
        tradee_nickname     TEXT,
        trader_gets         TEXT,
        tradee_gets         TEXT,
        trader_gets_pts_before  REAL,
        trader_gets_pts_after   REAL,
        tradee_gets_pts_before  REAL,
        tradee_gets_pts_after   REAL,
        point_diff          REAL,
        trade_winner_id     INTEGER,
        trade_winner        TEXT,
        trade_loser         TEXT
    );
""")
conn.commit()

league_end_weeks = {r["season"]: r["end_week"] for r in conn.execute("SELECT season, end_week FROM leagues").fetchall()}

trades = conn.execute("""
    SELECT t.transaction_key, t.season, t.league_key, t.timestamp,
           t.trader_team_key, t.tradee_team_key,
           o1.owner_id as trader_id, o1.nickname as trader,
           o2.owner_id as tradee_id, o2.nickname as tradee
    FROM transactions t
    JOIN team_owner_map m1 ON t.trader_team_key=m1.team_key
    JOIN owners o1 ON m1.owner_id=o1.owner_id
    JOIN team_owner_map m2 ON t.tradee_team_key=m2.team_key
    JOIN owners o2 ON m2.owner_id=o2.owner_id
    WHERE t.type='trade' AND t.status='successful'
    AND t.trader_team_key IS NOT NULL AND t.tradee_team_key IS NOT NULL
""").fetchall()

def get_pts(league_key, player_key, season, week_start, week_end):
    row = conn.execute("""
        SELECT SUM(CAST(fantasy_points AS REAL)) FROM player_weekly_stats
        WHERE league_key=? AND player_key=? AND season=?
        AND week >= ? AND week <= ? AND fantasy_points IS NOT NULL
    """, (league_key, player_key, season, week_start, week_end)).fetchone()
    return round(float(row[0] or 0), 2)

for t in trades:
    season = t["season"]
    ts = t["timestamp"]
    league_key = t["league_key"]
    end_week = league_end_weeks.get(season, 17)
    trade_date, trade_week = "unknown", 1

    if ts:
        try:
            dt = datetime.fromtimestamp(int(ts), tz=timezone.utc)
            trade_date = dt.strftime("%Y-%m-%d")
            season_start = datetime(season, 9, 7, tzinfo=timezone.utc)
            days_in = max(0, (dt - season_start).days)
            trade_week = min(max(1, days_in // 7 + 1), end_week)
        except Exception:
            pass

    players = conn.execute("""
        SELECT DISTINCT player_key, player_name, dest_team_key
        FROM transaction_players WHERE transaction_key=? AND player_key IS NOT NULL
    """, (t["transaction_key"],)).fetchall()

    trader_gets, tradee_gets = [], []
    seen = set()
    for p in players:
        key = (p["player_key"], p["dest_team_key"])
        if key in seen:
            continue
        seen.add(key)
        dest = p["dest_team_key"]
        if dest == t["trader_team_key"]:
            trader_gets.append((p["player_key"], p["player_name"]))
        elif dest == t["tradee_team_key"]:
            tradee_gets.append((p["player_key"], p["player_name"]))

    # Points BEFORE trade (weeks 1 through trade_week)
    # Points AFTER trade (weeks trade_week+1 through end_week)
    def side_pts(player_list, before=True):
        total = 0.0
        for pkey, _ in player_list:
            if before:
                total += get_pts(league_key, pkey, season, 1, trade_week)
            else:
                total += get_pts(league_key, pkey, season, trade_week + 1, end_week)
        return round(total, 2)

    tr_before = side_pts(trader_gets, before=True)
    tr_after  = side_pts(trader_gets, before=False)
    td_before = side_pts(tradee_gets, before=True)
    td_after  = side_pts(tradee_gets, before=False)

    # Lopsidedness = difference in AFTER points (what each side gained)
    diff = round(abs(tr_after - td_after), 2)
    winner = t["trader"] if tr_after >= td_after else t["tradee"]
    loser  = t["tradee"] if tr_after >= td_after else t["trader"]
    winner_id = t["trader_id"] if tr_after >= td_after else t["tradee_id"]

    conn.execute("""
        INSERT OR REPLACE INTO trade_summary VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        t["transaction_key"], season, trade_date, trade_week,
        t["trader_id"], t["tradee_id"], t["trader"], t["tradee"],
        json.dumps([n for _, n in trader_gets]),
        json.dumps([n for _, n in tradee_gets]),
        tr_before, tr_after, td_before, td_after,
        diff, winner_id, winner, loser
    ))

conn.commit()
print(f"Built {conn.execute('SELECT COUNT(*) FROM trade_summary').fetchone()[0]} trade summaries.")

print("\nTop 5 most lopsided trades (by rest-of-season points):")
for r in conn.execute("SELECT * FROM trade_summary ORDER BY point_diff DESC LIMIT 5").fetchall():
    tg = json.loads(r["trader_gets"] or "[]")
    dg = json.loads(r["tradee_gets"] or "[]")
    print(f"\n  {r['season']} {r['trade_date']}: {r['trader_nickname']} vs {r['tradee_nickname']}")
    print(f"    {r['trader_nickname']} got: {tg}")
    print(f"      Before trade: {r['trader_gets_pts_before']} pts | After: {r['trader_gets_pts_after']} pts")
    print(f"    {r['tradee_nickname']} got: {dg}")
    print(f"      Before trade: {r['tradee_gets_pts_before']} pts | After: {r['tradee_gets_pts_after']} pts")
    print(f"    Diff: {r['point_diff']} | WINNER: {r['trade_winner']}")

conn.close()
print("\nDone.")
