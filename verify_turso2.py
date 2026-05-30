import requests
TURSO_URL   = "https://lsn2k-guerillaradio.aws-us-east-2.turso.io"
TURSO_TOKEN = "eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9.eyJhIjoicnciLCJpYXQiOjE3ODAxNTE2MDksImlkIjoiMDE5ZTc5NDgtYWQwMS03ZmEyLWE4YzYtNDAyZjRkNWU2MTg0IiwicmlkIjoiODBiMjZkODUtOGI2MC00NWQwLWIyYTQtNDFlNmFiYWI0ODcwIn0.Pi0OoD5t8XuZp1Z45PaTX4ntJv3HuCWt0SWptoF9LOTSstbGw0MHa7PuWwK5SUJKCczKN6AC0EI87b3fs2XVAQ"
headers = {"Authorization": f"Bearer {TURSO_TOKEN}", "Content-Type": "application/json"}
def q(sql):
    payload = {"requests": [{"type": "execute", "stmt": {"sql": sql}}, {"type": "close"}]}
    resp = requests.post(f"{TURSO_URL}/v2/pipeline", headers=headers, json=payload, timeout=15)
    return resp.json()["results"][0]["response"]["result"]
r = q("SELECT COUNT(*) FROM final_standings")
print(f"final_standings rows in Turso: {r['rows'][0][0]['value']}")
r = q("SELECT o.nickname, fs.final_rank FROM final_standings fs JOIN owners o ON fs.owner_id=o.owner_id WHERE fs.season=2023 AND fs.final_rank<=3 ORDER BY fs.final_rank")
print("2023 top 3:")
for row in r["rows"]:
    print(f"  {row[1]['value']}. {row[0]['value']}")
