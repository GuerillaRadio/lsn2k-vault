import requests, sqlite3

TURSO_URL   = "https://lsn2k-guerillaradio.aws-us-east-2.turso.io"
TURSO_TOKEN = "eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9.eyJhIjoicnciLCJpYXQiOjE3ODAxNTE2MDksImlkIjoiMDE5ZTc5NDgtYWQwMS03ZmEyLWE4YzYtNDAyZjRkNWU2MTg0IiwicmlkIjoiODBiMjZkODUtOGI2MC00NWQwLWIyYTQtNDFlNmFiYWI0ODcwIn0.Pi0OoD5t8XuZp1Z45PaTX4ntJv3HuCWt0SWptoF9LOTSstbGw0MHa7PuWwK5SUJKCczKN6AC0EI87b3fs2XVAQ"
headers = {"Authorization": f"Bearer {TURSO_TOKEN}", "Content-Type": "application/json"}

def run(sql):
    payload = {"requests": [{"type": "execute", "stmt": {"sql": sql}}, {"type": "close"}]}
    resp = requests.post(f"{TURSO_URL}/v2/pipeline", headers=headers, json=payload, timeout=15)
    return resp.json()["results"][0]

local = sqlite3.connect("data/fantasy.db")
local.row_factory = sqlite3.Row

run("CREATE TABLE IF NOT EXISTS league_lore (id INTEGER PRIMARY KEY AUTOINCREMENT, season INTEGER, category TEXT NOT NULL, title TEXT NOT NULL, content TEXT NOT NULL, tags TEXT, created_at INTEGER DEFAULT (strftime('%s','now')))")

rows = local.execute("SELECT * FROM league_lore").fetchall()
for r in rows:
    content_escaped = r['content'].replace("'", "''")
    title_escaped = r['title'].replace("'", "''")
    tags = r['tags'] or ''
    season = str(r['season']) if r['season'] else 'NULL'
    sql = f"INSERT OR IGNORE INTO league_lore (id, season, category, title, content, tags) VALUES ({r['id']}, {season}, '{r['category']}', '{title_escaped}', '{content_escaped}', '{tags}')"
    result = run(sql)
    print(f"  [{r['id']}] {r['title']}: {result.get('type')}")

local.close()
print(f"\nPushed {len(rows)} lore entries to Turso.")
