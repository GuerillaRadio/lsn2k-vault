import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))
from database import get_conn
conn = get_conn()

print("Dusty in final_standings:")
for r in conn.execute("""
    SELECT fs.season, fs.final_rank, fs.playoff_result
    FROM final_standings fs JOIN owners o ON fs.owner_id=o.owner_id
    WHERE o.nickname='Dusty' ORDER BY fs.season
""").fetchall():
    print(f"  {r['season']}: rank {r['final_rank']} ({r['playoff_result']})")

print("\nTop-4 count:", conn.execute("""
    SELECT COUNT(*) FROM final_standings fs JOIN owners o ON fs.owner_id=o.owner_id
    WHERE o.nickname='Dusty' AND fs.final_rank <= 4
""").fetchone()[0])

print("\nDuplicates check:")
n = conn.execute("""
    SELECT COUNT(*) FROM final_standings fs JOIN owners o ON fs.owner_id=o.owner_id
    WHERE o.nickname='Dusty'
""").fetchone()[0]
print(f"  Total Dusty rows in final_standings: {n} (should be 23)")
conn.close()
