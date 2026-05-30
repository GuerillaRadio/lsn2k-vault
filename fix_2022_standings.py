import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))
from database import get_conn
conn = get_conn()

# Fix Nic's 2022 final_standings — should be co-champion rank 1, not runner-up rank 2
nic_id = conn.execute("SELECT owner_id FROM owners WHERE nickname='Nic'").fetchone()["owner_id"]
conn.execute("""
    UPDATE final_standings SET final_rank=1, playoff_result='co-champion (tied 85.5-85.5)'
    WHERE season=2022 AND owner_id=?
""", (nic_id,))

scott_id = conn.execute("SELECT owner_id FROM owners WHERE nickname='Scott'").fetchone()["owner_id"]
conn.execute("""
    UPDATE final_standings SET playoff_result='co-champion (tied 85.5-85.5)'
    WHERE season=2022 AND owner_id=?
""", (scott_id,))

conn.commit()
print("Fixed 2022 co-championship in final_standings")

print("\n2022 final_standings:")
for r in conn.execute("""
    SELECT fs.final_rank, o.nickname, fs.playoff_result
    FROM final_standings fs JOIN owners o ON fs.owner_id=o.owner_id
    WHERE fs.season=2022 ORDER BY fs.final_rank LIMIT 5
""").fetchall():
    print(f"  {r['final_rank']}. {r['nickname']} — {r['playoff_result']}")

conn.close()
