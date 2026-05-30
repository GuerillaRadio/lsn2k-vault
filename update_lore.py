import sys, requests, sqlite3
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))
from database import get_conn

# Update locally
conn = get_conn()
conn.execute("""
    UPDATE league_lore SET content=? WHERE id=1
""", ("Back in high school, Dustin Butler called Coach Taylor a dickhead to his face in front of the whole team during practice. Coach wrote him up on the spot — green slip, sent straight to Principal Stan Elliott's office. Dusty has never lived it down. Coach brings it up whenever Dusty questions him, talks back, or has a bad season. To this day it remains the gold standard green slip in Coach Taylor's disciplinary career, and he considers it one of his finest moments. Stan Elliott framed the incident report.",))
conn.commit()
conn.close()
print("Updated locally")

# Push update to Turso
TURSO_URL   = "https://lsn2k-guerillaradio.aws-us-east-2.turso.io"
TURSO_TOKEN = "eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9.eyJhIjoicnciLCJpYXQiOjE3ODAxNTE2MDksImlkIjoiMDE5ZTc5NDgtYWQwMS03ZmEyLWE4YzYtNDAyZjRkNWU2MTg0IiwicmlkIjoiODBiMjZkODUtOGI2MC00NWQwLWIyYTQtNDFlNmFiYWI0ODcwIn0.Pi0OoD5t8XuZp1Z45PaTX4ntJv3HuCWt0SWptoF9LOTSstbGw0MHa7PuWwK5SUJKCczKN6AC0EI87b3fs2XVAQ"
headers = {"Authorization": f"Bearer {TURSO_TOKEN}", "Content-Type": "application/json"}
new_content = "Back in high school, Dustin Butler called Coach Taylor a dickhead to his face in front of the whole team during practice. Coach wrote him up on the spot — green slip, sent straight to Principal Stan Elliott''s office. Dusty has never lived it down. Coach brings it up whenever Dusty questions him, talks back, or has a bad season. To this day it remains the gold standard green slip in Coach Taylor''s disciplinary career, and he considers it one of his finest moments. Stan Elliott framed the incident report."
sql = f"UPDATE league_lore SET content='{new_content}' WHERE id=1"
payload = {"requests": [{"type": "execute", "stmt": {"sql": sql}}, {"type": "close"}]}
resp = requests.post(f"{TURSO_URL}/v2/pipeline", headers=headers, json=payload, timeout=15)
print(f"Turso: {resp.json()['results'][0].get('type')}")
