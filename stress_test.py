import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))
from database import get_conn
conn = get_conn()

print("="*60)
print("1. MOST CHAMPIONSHIPS + YEARS")
print("="*60)
for r in conn.execute("""
    SELECT o.nickname, COUNT(*) as rings,
           GROUP_CONCAT(c.season || CASE WHEN c.note LIKE '%co%' THEN '*' ELSE '' END, ', ') as years
    FROM championships c JOIN owners o ON c.owner_id=o.owner_id
    GROUP BY o.owner_id ORDER BY rings DESC
""").fetchall():
    print(f"  {r['nickname']}: {r['rings']} — {r['years']}")
print("  (* = co-champion)")

print("\n" + "="*60)
print("2. FALK vs SCOTT HEAD-TO-HEAD")
print("="*60)
r = conn.execute("""
    SELECT o1.nickname, h.wins, h.losses, h.ties, h.points_for, h.points_against
    FROM owner_h2h h
    JOIN owners o1 ON h.owner1_id=o1.owner_id
    JOIN owners o2 ON h.owner2_id=o2.owner_id
    WHERE o1.nickname='Falk' AND o2.nickname='Scott'
""").fetchone()
wins, losses = int(r['wins']), int(r['losses'])
leader = 'Falk' if wins > losses else ('Scott' if losses > wins else 'Tied')
print(f"  Falk: {wins}W-{losses}L  |  Leader: {leader}")

print("\n" + "="*60)
print("3. TRADES")
print("="*60)
trade_count = conn.execute("SELECT COUNT(*) FROM transactions WHERE type='trade' AND status='successful'").fetchone()[0]
print(f"  Total successful trades: {trade_count}")
print("  5 most recent:")
trades = conn.execute("""
    SELECT t.season, trader.nickname as tr, tradee.nickname as te, t.transaction_key
    FROM transactions t
    JOIN team_owner_map m1 ON t.trader_team_key=m1.team_key
    JOIN owners trader ON m1.owner_id=trader.owner_id
    JOIN team_owner_map m2 ON t.tradee_team_key=m2.team_key
    JOIN owners tradee ON m2.owner_id=tradee.owner_id
    WHERE t.type='trade' AND t.status='successful'
    ORDER BY t.timestamp DESC LIMIT 5
""").fetchall()
for t in trades:
    players = conn.execute("SELECT player_name FROM transaction_players WHERE transaction_key=? LIMIT 4", (t['transaction_key'],)).fetchall()
    names = [p['player_name'] for p in players]
    print(f"  {t['season']}: {t['tr']} <-> {t['te']}: {names}")

print("\n" + "="*60)
print("4. DUSTY TOP-4 FINISHES")
print("="*60)
r = conn.execute("""
    SELECT COUNT(*) as n, MIN(final_rank) as best
    FROM final_standings fs JOIN owners o ON fs.owner_id=o.owner_id
    WHERE o.nickname='Dusty' AND fs.final_rank <= 4
""").fetchone()
details = conn.execute("""
    SELECT season, final_rank, playoff_result FROM final_standings fs
    JOIN owners o ON fs.owner_id=o.owner_id
    WHERE o.nickname='Dusty' AND fs.final_rank <= 4 ORDER BY final_rank, season
""").fetchall()
print(f"  Top-4 finishes: {r['n']}  |  Best: #{r['best']}")
for d in details:
    print(f"  {d['season']}: #{d['final_rank']} ({d['playoff_result']})")

print("\n" + "="*60)
print("5. 2019 REGULAR SEASON POINTS")
print("="*60)
for r in conn.execute("""
    SELECT o.nickname, oss.points_for, oss.wins, oss.losses
    FROM owner_season_stats oss JOIN owners o ON oss.owner_id=o.owner_id
    WHERE oss.season=2019 ORDER BY oss.points_for DESC
""").fetchall():
    pts = float(r['points_for'] or 0)
    print(f"  {r['nickname']}: {pts:.2f} pts, {r['wins']}-{r['losses']}")

conn.close()
