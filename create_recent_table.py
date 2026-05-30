import requests

TURSO_URL   = "https://lsn2k-guerillaradio.aws-us-east-2.turso.io"
TURSO_TOKEN = "eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9.eyJhIjoicnciLCJpYXQiOjE3ODAxNTE2MDksImlkIjoiMDE5ZTc5NDgtYWQwMS03ZmEyLWE4YzYtNDAyZjRkNWU2MTg0IiwicmlkIjoiODBiMjZkODUtOGI2MC00NWQwLWIyYTQtNDFlNmFiYWI0ODcwIn0.Pi0OoD5t8XuZp1Z45PaTX4ntJv3HuCWt0SWptoF9LOTSstbGw0MHa7PuWwK5SUJKCczKN6AC0EI87b3fs2XVAQ"
headers = {"Authorization": f"Bearer {TURSO_TOKEN}", "Content-Type": "application/json"}

def run(sql):
    payload = {"requests": [{"type": "execute", "stmt": {"sql": sql}}, {"type": "close"}]}
    resp = requests.post(f"{TURSO_URL}/v2/pipeline", headers=headers, json=payload, timeout=15)
    resp.raise_for_status()
    return resp.json()["results"][0]["response"]["result"]

# Create table
run("""CREATE TABLE IF NOT EXISTS recent_queries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question TEXT NOT NULL,
    asked_at INTEGER DEFAULT (strftime('%s','now'))
)""")
print("Table created")

# Check what's in it
result = run("SELECT COUNT(*) FROM recent_queries")
print(f"Current rows: {result['rows'][0][0]['value']}")

result = run("SELECT question FROM recent_queries ORDER BY asked_at DESC LIMIT 5")
if result['rows']:
    print("Recent queries:")
    for row in result['rows']:
        print(f"  - {row[0]['value']}")
else:
    print("No queries yet")
