import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))
from database import get_conn
conn = get_conn()

# Check for duplicate transaction_players
n = conn.execute("""
    SELECT COUNT(*) FROM transaction_players
""").fetchone()[0]
n_distinct = conn.execute("""
    SELECT COUNT(*) FROM (
        SELECT DISTINCT transaction_key, player_key, transaction_type FROM transaction_players
    )
""").fetchone()[0]
print(f"Total rows: {n}, Distinct: {n_distinct}, Dupes: {n - n_distinct}")

# Rebuild trade_summary with deduplication
conn.execute("DROP TABLE IF EXISTS trade_summary")
conn.executescript("""
    CREATE TABLE trade_summary (
        transaction_key TEXT PRIMARY KEY, season INTEGER, trade_date TEXT,
        trade_week INTEGER, trader_owner_id INTEGER, tradee_owner_id INTEGER,
        trader_nickname TEXT, tradee_nickname TEXT,
        trader_gets TEXT, tradee_gets TEXT,
        trader_pts_gained REAL, tradee_pts_gained REAL,
        point_diff REAL, trade_winner_id INTEGER, trade_winner TEXT, trade_loser TEXT
    );
""")
conn.commit()

from datetime import datetime, timezone
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

for t in trades:
    season = t["season"]
    ts = t["timestamp"]
    league_key = t["league_key"]
    trade_date, trade_week = "unknown", 1
    if ts:
        try:
            dt = datetime.fromtimestamp(int(ts), tz=timezone.utc)
            trade_date = dt.strftime("%Y-%m-%d")
            season_start = datetime(season, 9, 7, tzinfo=timezone.utc)
            days_in = max(0, (dt - season_start).days)
            trade_week = min(max(1, days_in // 7 + 1), league_end_weeks.get(season, 17))
        except Exception:
            pass

    # DEDUPLICATE players by (player_key, dest_team_key)
    players = conn.execute("""
        SELECT DISTINCT player_key, player_name, dest_team_key
        FROM transaction_players WHERE transaction_key=?
        AND player_key IS NOT NULL
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

    def season_pts(player_list):
        total = 0.0
        for pkey, _ in player_list:
            row = conn.execute("""
                SELECT SUM(CAST(fantasy_points AS REAL)) FROM player_weekly_stats
                WHERE league_key=? AND player_key=? AND season=? AND week > ?
                AND fantasy_points IS NOT NULL
            """, (league_key, pkey, season, trade_week)).fetchone()
            if row and row[0]:
                total += float(row[0])
        return round(total, 2)

    trader_pts = season_pts(trader_gets)
    tradee_pts = season_pts(tradee_gets)
    diff = round(abs(trader_pts - tradee_pts), 2)
    winner_id = t["trader_id"] if trader_pts >= tradee_pts else t["tradee_id"]
    winner = t["trader"] if trader_pts >= tradee_pts else t["tradee"]
    loser = t["tradee"] if trader_pts >= tradee_pts else t["trader"]

    conn.execute("""
        INSERT OR REPLACE INTO trade_summary
            (transaction_key, season, trade_date, trade_week,
             trader_owner_id, tradee_owner_id, trader_nickname, tradee_nickname,
             trader_gets, tradee_gets, trader_pts_gained, tradee_pts_gained,
             point_diff, trade_winner_id, trade_winner, trade_loser)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        t["transaction_key"], season, trade_date, trade_week,
        t["trader_id"], t["tradee_id"], t["trader"], t["tradee"],
        json.dumps([n for _, n in trader_gets]),
        json.dumps([n for _, n in tradee_gets]),
        trader_pts, tradee_pts, diff, winner_id, winner, loser
    ))

conn.commit()
print(f"\nRebuilt {conn.execute('SELECT COUNT(*) FROM trade_summary').fetchone()[0]} trade summaries.")

print("\nTop 5 most lopsided trades:")
for r in conn.execute("SELECT * FROM trade_summary ORDER BY point_diff DESC LIMIT 5").fetchall():
    tg = json.loads(r["trader_gets"] or "[]")
    dg = json.loads(r["tradee_gets"] or "[]")
    print(f"  {r['season']} {r['trade_date']}: {r['trader_nickname']} vs {r['tradee_nickname']}")
    print(f"    {r['trader_nickname']} got: {tg} ({r['trader_pts_gained']} pts)")
    print(f"    {r['tradee_nickname']} got: {dg} ({r['tradee_pts_gained']} pts)")
    print(f"    Diff: {r['point_diff']} | WINNER: {r['trade_winner']}")

conn.close()
