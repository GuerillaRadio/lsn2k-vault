import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))
from database import get_conn
conn = get_conn()

print("Full championships table:")
for r in conn.execute("""
    SELECT c.season, o.nickname, c.note
    FROM championships c JOIN owners o ON c.owner_id=o.owner_id
    ORDER BY c.season, o.nickname
""").fetchall():
    print(f"  {r['season']}: {r['nickname']} — {r['note'] or ''}")

print("\nAny seasons with more than one entry (should only be 2022):")
for r in conn.execute("""
    SELECT season, COUNT(*) as n FROM championships GROUP BY season HAVING n > 1
""").fetchall():
    print(f"  {r['season']}: {r['n']} entries")

print("\n2022 in final_standings:")
for r in conn.execute("""
    SELECT fs.final_rank, o.nickname, fs.playoff_result
    FROM final_standings fs JOIN owners o ON fs.owner_id=o.owner_id
    WHERE fs.season=2022 ORDER BY fs.final_rank
""").fetchall():
    print(f"  {r['final_rank']}. {r['nickname']} — {r['playoff_result']}")
conn.close()
