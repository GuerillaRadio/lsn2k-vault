"""
Pre-compute trade analytics — one row per trade with:
- who was involved, what was traded
- how each side's players scored for the REST of that season after the trade
- point differential (who won the trade)
"""
import sys, json
from pathlib import Path
from datetime import datetime, timezone
sys.path.insert(0, str(Path(__file__).parent / "src"))
from database import get_conn

conn = get_conn()

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
        trader_gets         TEXT,  -- JSON list of player names received by trader
        tradee_gets         TEXT,  -- JSON list of player names received by tradee
        trader_pts_gained   REAL,  -- season pts of players trader received (after trade)
        tradee_pts_gained   REAL,  -- season pts of players tradee received (after trade)
        point_diff          REAL,  -- abs(trader_pts_gained - tradee_pts_gained)
        trade_winner_id     INTEGER,
        trade_winner        TEXT,
        trade_loser         TEXT,
        notes               TEXT
    );
""")
conn.commit()

# Get all successful trades
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

print(f"Processing {len(trades)} trades...")

# Get league end weeks for reference
league_end_weeks = {r["season"]: r["end_week"] for r in conn.execute("SELECT season, end_week FROM leagues").fetchall()}

for t in trades:
    season = t["season"]
    ts = t["timestamp"]
    league_key = t["league_key"]

    # Convert timestamp to approximate NFL week
    trade_date = "unknown"
    trade_week = 1
    if ts:
        try:
            dt = datetime.fromtimestamp(int(ts), tz=timezone.utc)
            trade_date = dt.strftime("%Y-%m-%d")
            # Approximate week: NFL season starts ~week 1 of September
            # Each week is ~7 days; season starts around Sept 7
            season_start = datetime(season, 9, 7, tzinfo=timezone.utc)
            days_in = max(0, (dt - season_start).days)
            trade_week = min(max(1, days_in // 7 + 1), league_end_weeks.get(season, 17))
        except Exception:
            pass

    # Get players in this trade
    players = conn.execute("""
        SELECT tp.player_key, tp.player_name, tp.transaction_type,
               tp.source_team_key, tp.dest_team_key
        FROM transaction_players tp
        WHERE tp.transaction_key=?
    """, (t["transaction_key"],)).fetchall()

    # Figure out who got what
    # dest_team_key tells us where the player went
    trader_gets = []   # players who went TO the trader's team
    tradee_gets = []   # players who went TO the tradee's team

    for p in players:
        dest = p["dest_team_key"]
        if dest == t["trader_team_key"]:
            trader_gets.append((p["player_key"], p["player_name"]))
        elif dest == t["tradee_team_key"]:
            tradee_gets.append((p["player_key"], p["player_name"]))
        else:
            # Fall back to transaction_type
            if p["transaction_type"] == "add":
                trader_gets.append((p["player_key"], p["player_name"]))
            else:
                tradee_gets.append((p["player_key"], p["player_name"]))

    # Calculate season points for each side AFTER the trade week
    def season_pts(player_list):
        total = 0.0
        for pkey, _ in player_list:
            if not pkey:
                continue
            rows = conn.execute("""
                SELECT SUM(CAST(fantasy_points AS REAL)) FROM player_weekly_stats
                WHERE league_key=? AND player_key=? AND season=? AND week > ?
                AND fantasy_points IS NOT NULL
            """, (league_key, pkey, season, trade_week)).fetchone()
            if rows and rows[0]:
                total += float(rows[0])
        return round(total, 2)

    trader_pts = season_pts(trader_gets)
    tradee_pts = season_pts(tradee_gets)
    diff = round(abs(trader_pts - tradee_pts), 2)

    if trader_pts >= tradee_pts:
        winner_id = t["trader_id"]
        winner = t["trader"]
        loser = t["tradee"]
    else:
        winner_id = t["tradee_id"]
        winner = t["tradee"]
        loser = t["trader"]

    conn.execute("""
        INSERT OR REPLACE INTO trade_summary
            (transaction_key, season, trade_date, trade_week,
             trader_owner_id, tradee_owner_id, trader_nickname, tradee_nickname,
             trader_gets, tradee_gets,
             trader_pts_gained, tradee_pts_gained, point_diff,
             trade_winner_id, trade_winner, trade_loser)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        t["transaction_key"], season, trade_date, trade_week,
        t["trader_id"], t["tradee_id"], t["trader"], t["tradee"],
        json.dumps([n for _, n in trader_gets]),
        json.dumps([n for _, n in tradee_gets]),
        trader_pts, tradee_pts, diff,
        winner_id, winner, loser
    ))

conn.commit()
total = conn.execute("SELECT COUNT(*) FROM trade_summary").fetchone()[0]
print(f"Built {total} trade summaries.")

print("\nTop 10 most lopsided trades:")
for r in conn.execute("""
    SELECT season, trade_date, trader_nickname, tradee_nickname,
           trader_gets, tradee_gets,
           trader_pts_gained, tradee_pts_gained, point_diff,
           trade_winner, trade_loser
    FROM trade_summary
    WHERE point_diff > 0
    ORDER BY point_diff DESC LIMIT 10
""").fetchall():
    tg = json.loads(r["trader_gets"] or "[]")
    dg = json.loads(r["tradee_gets"] or "[]")
    print(f"\n  {r['season']} ({r['trade_date']}): {r['trader_nickname']} <-> {r['tradee_nickname']}")
    print(f"    {r['trader_nickname']} got: {tg} → {r['trader_pts_gained']} pts")
    print(f"    {r['tradee_nickname']} got: {dg} → {r['tradee_pts_gained']} pts")
    print(f"    Diff: {r['point_diff']} pts | Winner: {r['trade_winner']}")

conn.close()
print("\nDone.")
