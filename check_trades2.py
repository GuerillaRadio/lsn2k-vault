import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))
from database import get_conn
conn = get_conn()

print("Top 10 most lopsided trades:")
for r in conn.execute("""
    SELECT season, trade_date, trader_nickname, tradee_nickname,
           trader_gets, tradee_gets, trader_pts_gained, tradee_pts_gained,
           point_diff, trade_winner, trade_loser
    FROM trade_summary WHERE point_diff > 0
    ORDER BY point_diff DESC LIMIT 10
""").fetchall():
    tg = json.loads(r["trader_gets"] or "[]")
    dg = json.loads(r["tradee_gets"] or "[]")
    print(f"\n  {r['season']} {r['trade_date']}: {r['trader_nickname']} vs {r['tradee_nickname']}")
    print(f"    {r['trader_nickname']} got: {tg} ({r['trader_pts_gained']} pts)")
    print(f"    {r['tradee_nickname']} got: {dg} ({r['tradee_pts_gained']} pts)")
    print(f"    Diff: {r['point_diff']} | WINNER: {r['trade_winner']}")

print(f"\nTotal trades: {conn.execute('SELECT COUNT(*) FROM trade_summary').fetchone()[0]}")
conn.close()
