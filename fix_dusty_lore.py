import sys, requests, sqlite3
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))
from database import get_conn

NEW_CONTENT = ("Back in high school, Dustin Butler called a friend a dickhead in the hallway. "
               "Coach Taylor overheard it, immediately wrote him up on a green slip, and marched him "
               "straight to Principal Stan Elliott's office. On the way there, Dusty — furious at being "
               "ratted out for something that had nothing to do with Coach — turned around and called "
               "Taylor a cocksucker to his face. Right there in the hallway. In front of everyone. "
               "Coach Taylor has never forgotten it. He brings it up constantly. "
               "It is, by his own account, the greatest disciplinary moment of his career. "
               "Stan Elliott still has the incident report in a filing cabinet.")

# Update local
conn = get_conn()
conn.execute("UPDATE league_lore SET content=? WHERE id=1", (NEW_CONTENT,))
conn.commit()
conn.close()
print("Updated locally")

# Update Turso
TURSO_URL   = "https://lsn2k-guerillaradio.aws-us-east-2.turso.io"
TURSO_TOKEN = "eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9.eyJhIjoicnciLCJpYXQiOjE3ODAxNTE2MDksImlkIjoiMDE5ZTc5NDgtYWQwMS03ZmEyLWE4YzYtNDAyZjRkNWU2MTg0IiwicmlkIjoiODBiMjZkODUtOGI2MC00NWQwLWIyYTQtNDFlNmFiYWI0ODcwIn0.Pi0OoD5t8XuZp1Z45PaTX4ntJv3HuCWt0SWptoF9LOTSstbGw0MHa7PuWwK5SUJKCczKN6AC0EI87b3fs2XVAQ"
headers = {"Authorization": f"Bearer {TURSO_TOKEN}", "Content-Type": "application/json"}
escaped = NEW_CONTENT.replace("'", "''")
sql = f"UPDATE league_lore SET content='{escaped}' WHERE id=1"
payload = {"requests": [{"type": "execute", "stmt": {"sql": sql}}, {"type": "close"}]}
resp = requests.post(f"{TURSO_URL}/v2/pipeline", headers=headers, json=payload, timeout=15)
print(f"Turso: {resp.json()['results'][0].get('type')}")
