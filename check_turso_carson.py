import requests, json

TURSO_URL   = "https://lsn2k-guerillaradio.aws-us-east-2.turso.io"
TURSO_TOKEN = "eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9.eyJhIjoicnciLCJpYXQiOjE3ODAxNTE2MDksImlkIjoiMDE5ZTc5NDgtYWQwMS03ZmEyLWE4YzYtNDAyZjRkNWU2MTg0IiwicmlkIjoiODBiMjZkODUtOGI2MC00NWQwLWIyYTQtNDFlNmFiYWI0ODcwIn0.Pi0OoD5t8XuZp1Z45PaTX4ntJv3HuCWt0SWptoF9LOTSstbGw0MHa7PuWwK5SUJKCczKN6AC0EI87b3fs2XVAQ"
headers = {"Authorization": f"Bearer {TURSO_TOKEN}", "Content-Type": "application/json"}

def q(sql):
    payload = {"requests": [{"type": "execute", "stmt": {"sql": sql}}, {"type": "close"}]}
    resp = requests.post(f"{TURSO_URL}/v2/pipeline", headers=headers, json=payload, timeout=15)
    return resp.json()["results"][0]["response"]["result"]

# Check consolation flags in Turso
print("Playoff matchup counts in Turso by is_consolation flag:")
r = q("SELECT is_consolation, COUNT(*) as n FROM matchups WHERE is_playoffs=1 GROUP BY is_consolation")
for row in r["rows"]:
    print(f"  is_consolation={row[0]['value']}: {row[1]['value']} games")

print("\nCarson final-week playoff games in Turso (no consolation filter):")
r = q("""
    SELECT m.season, m.week, m.is_consolation,
           m.team1_points, m.team2_points, m.winner_team_key
    FROM matchups m
    JOIN team_owner_map map1 ON m.team1_key=map1.team_key
    JOIN owners o1 ON map1.owner_id=o1.owner_id
    JOIN leagues l ON m.league_key=l.league_key
    WHERE o1.nickname='Carson' AND m.is_playoffs=1 AND m.week=l.end_week
    ORDER BY m.season
""")
for row in r["rows"]:
    print(f"  {row[0]['value']} wk{row[1]['value']}: consolation={row[2]['value']}")
