import requests

TURSO_URL   = "https://lsn2k-guerillaradio.aws-us-east-2.turso.io"
TURSO_TOKEN = "eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9.eyJhIjoicnciLCJpYXQiOjE3ODAxNTE2MDksImlkIjoiMDE5ZTc5NDgtYWQwMS03ZmEyLWE4YzYtNDAyZjRkNWU2MTg0IiwicmlkIjoiODBiMjZkODUtOGI2MC00NWQwLWIyYTQtNDFlNmFiYWI0ODcwIn0.Pi0OoD5t8XuZp1Z45PaTX4ntJv3HuCWt0SWptoF9LOTSstbGw0MHa7PuWwK5SUJKCczKN6AC0EI87b3fs2XVAQ"

headers = {"Authorization": f"Bearer {TURSO_TOKEN}", "Content-Type": "application/json"}

def query(sql):
    payload = {"requests": [{"type": "execute", "stmt": {"sql": sql}}, {"type": "close"}]}
    resp = requests.post(f"{TURSO_URL}/v2/pipeline", headers=headers, json=payload, timeout=15)
    resp.raise_for_status()
    result = resp.json()["results"][0]["response"]["result"]
    return result

tables = [
    "championships", "draft_picks", "leagues", "matchups", "owners",
    "owner_all_time", "owner_season_stats", "owner_h2h", "player_weekly_stats",
    "players", "roster_slots", "roster_positions", "scoring_settings",
    "standings", "stat_categories", "team_owner_map", "teams",
    "transaction_players", "transactions", "weekly_high_scores"
]

print("Turso row counts:")
total_remote = 0
for table in tables:
    try:
        r = query(f"SELECT COUNT(*) FROM {table}")
        count = int(r["rows"][0][0]["value"])
        total_remote += count
        print(f"  {table}: {count:,}")
    except Exception as e:
        print(f"  {table}: ERROR - {e}")

print(f"\nTotal rows in Turso: {total_remote:,}")

# Spot check a few records
print("\nSample data:")
r = query("SELECT o.full_name, c.season FROM championships c JOIN owners o ON c.owner_id=o.owner_id ORDER BY c.season LIMIT 5")
for row in r["rows"]:
    print(f"  {row[1]['value']}: {row[0]['value']}")
