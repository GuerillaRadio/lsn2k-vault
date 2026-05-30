import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))
from database import get_conn
conn = get_conn()

print("Trade counts by status:")
for r in conn.execute("SELECT status, COUNT(*) as n FROM transactions WHERE type='trade' GROUP BY status ORDER BY n DESC").fetchall():
    print(f"  {r['status']}: {r['n']}")

print("\nTotal trades:", conn.execute("SELECT COUNT(*) FROM transactions WHERE type='trade'").fetchone()[0])
print("Accepted trades:", conn.execute("SELECT COUNT(*) FROM transactions WHERE type='trade' AND status='successful'").fetchone()[0])

print("\nSample trades (any status):")
for r in conn.execute("""
    SELECT t.season, t.status, t.timestamp,
           GROUP_CONCAT(tp.player_name || ' (' || tp.transaction_type || ')') as players
    FROM transactions t
    JOIN transaction_players tp ON t.transaction_key=tp.transaction_key
    WHERE t.type='trade'
    GROUP BY t.transaction_key
    ORDER BY t.season DESC LIMIT 5
""").fetchall():
    print(f"  {r['season']} [{r['status']}]: {r['players']}")
conn.close()
