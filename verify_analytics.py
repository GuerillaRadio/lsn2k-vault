import requests
TURSO_URL   = "https://lsn2k-guerillaradio.aws-us-east-2.turso.io"
TURSO_TOKEN = "eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9.eyJhIjoicnciLCJpYXQiOjE3ODAxNTE2MDksImlkIjoiMDE5ZTc5NDgtYWQwMS03ZmEyLWE4YzYtNDAyZjRkNWU2MTg0IiwicmlkIjoiODBiMjZkODUtOGI2MC00NWQwLWIyYTQtNDFlNmFiYWI0ODcwIn0.Pi0OoD5t8XuZp1Z45PaTX4ntJv3HuCWt0SWptoF9LOTSstbGw0MHa7PuWwK5SUJKCczKN6AC0EI87b3fs2XVAQ"
headers = {"Authorization": f"Bearer {TURSO_TOKEN}", "Content-Type": "application/json"}

def q(sql):
    payload = {"requests": [{"type": "execute", "stmt": {"sql": sql}}, {"type": "close"}]}
    r = requests.post(f"{TURSO_URL}/v2/pipeline", headers=headers, json=payload, timeout=15)
    return r.json()["results"][0]["response"]["result"]

tables = [
    "matchup_results", "owner_playoff_stats", "waiver_summary",
    "bench_points", "draft_pick_value", "owner_streaks",
    "season_awards", "owner_vs_owner", "trade_summary", "final_standings"
]

print("Analytics tables in Turso:")
total = 0
for t in tables:
    try:
        r = q(f"SELECT COUNT(*) FROM {t}")
        n = int(r["rows"][0][0]["value"])
        total += n
        print(f"  {t}: {n:,}")
    except Exception as e:
        print(f"  {t}: ERROR - {e}")

print(f"\nTotal analytics rows: {total:,}")
