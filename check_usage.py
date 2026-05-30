import requests
TURSO_URL   = "https://lsn2k-guerillaradio.aws-us-east-2.turso.io"
TURSO_TOKEN = "eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9.eyJhIjoicnciLCJpYXQiOjE3ODAxNTE2MDksImlkIjoiMDE5ZTc5NDgtYWQwMS03ZmEyLWE4YzYtNDAyZjRkNWU2MTg0IiwicmlkIjoiODBiMjZkODUtOGI2MC00NWQwLWIyYTQtNDFlNmFiYWI0ODcwIn0.Pi0OoD5t8XuZp1Z45PaTX4ntJv3HuCWt0SWptoF9LOTSstbGw0MHa7PuWwK5SUJKCczKN6AC0EI87b3fs2XVAQ"
headers = {"Authorization": f"Bearer {TURSO_TOKEN}", "Content-Type": "application/json"}
def q(sql):
    payload = {"requests": [{"type": "execute", "stmt": {"sql": sql}}, {"type": "close"}]}
    r = requests.post(f"{TURSO_URL}/v2/pipeline", headers=headers, json=payload, timeout=15)
    return r.json()["results"][0]["response"]["result"]
r = q("SELECT COUNT(*) FROM usage_log")
print("usage_log rows:", r["rows"][0][0]["value"])
r = q("SELECT model, input_tokens, output_tokens, cost_usd, asked_at FROM usage_log ORDER BY asked_at DESC LIMIT 5")
if r["rows"]:
    for row in r["rows"]:
        print([c["value"] for c in row])
else:
    print("No rows yet")
