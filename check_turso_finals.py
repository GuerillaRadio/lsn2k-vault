import requests

TURSO_URL   = "https://lsn2k-guerillaradio.aws-us-east-2.turso.io"
TURSO_TOKEN = "eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9.eyJhIjoicnciLCJpYXQiOjE3ODAxNTE2MDksImlkIjoiMDE5ZTc5NDgtYWQwMS03ZmEyLWE4YzYtNDAyZjRkNWU2MTg0IiwicmlkIjoiODBiMjZkODUtOGI2MC00NWQwLWIyYTQtNDFlNmFiYWI0ODcwIn0.Pi0OoD5t8XuZp1Z45PaTX4ntJv3HuCWt0SWptoF9LOTSstbGw0MHa7PuWwK5SUJKCczKN6AC0EI87b3fs2XVAQ"
headers = {"Authorization": f"Bearer {TURSO_TOKEN}", "Content-Type": "application/json"}

def q(sql):
    payload = {"requests": [{"type": "execute", "stmt": {"sql": sql}}, {"type": "close"}]}
    resp = requests.post(f"{TURSO_URL}/v2/pipeline", headers=headers, json=payload, timeout=15)
    return resp.json()["results"][0]["response"]["result"]

print("Consolation flag counts in Turso:")
r = q("SELECT is_consolation, COUNT(*) FROM matchups WHERE is_playoffs=1 GROUP BY is_consolation")
for row in r["rows"]:
    print(f"  is_consolation={row[0]['value']}: {row[1]['value']}")

print("\nFinal-week non-consolation playoff games per season in Turso:")
r = q("""
    SELECT season, COUNT(*) as n FROM matchups
    WHERE is_playoffs=1 AND is_consolation=0
    AND week IN (SELECT end_week FROM leagues WHERE leagues.league_key=matchups.league_key)
    GROUP BY season ORDER BY season
""")
for row in r["rows"]:
    flag = " <-- WRONG" if int(row[1]['value']) != 1 else ""
    print(f"  {row[0]['value']}: {row[1]['value']}{flag}")
