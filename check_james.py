import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))
from database import get_conn
conn = get_conn()

print("Championships table:")
for r in conn.execute("SELECT c.season, o.nickname, c.note FROM championships c JOIN owners o ON c.owner_id=o.owner_id ORDER BY c.season").fetchall():
    print(f"  {r['season']}: {r['nickname']}")

print("\nJames in owner_all_time:")
r = conn.execute("SELECT nickname, championships, seasons_played FROM owner_all_time WHERE nickname='James'").fetchone()
print(f"  {r['nickname']}: {r['championships']} championships, {r['seasons_played']} seasons")

print("\nResponse cache entries (could be stale):")
n = conn.execute("SELECT COUNT(*) FROM response_cache").fetchone()[0]
print(f"  {n} cached responses")
conn.close()
