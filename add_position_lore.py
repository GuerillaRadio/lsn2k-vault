import sys, requests, sqlite3
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))
from database import get_conn

LORE = {
    "season": None,
    "category": "milestone",
    "title": "Position Value Analysis — What Actually Wins Championships",
    "content": (
        "Across 23 seasons of league history, the data reveals what separates champions from everyone else.\n\n"
        "TE is the most critical differentiating position. Champions average 1.44 more points per week from "
        "their TE than non-champions — the largest edge of any position. An elite tight end is a bigger "
        "competitive advantage in this league than an elite QB, RB, or WR.\n\n"
        "RB is the second most important edge (+1.06 pts/week), followed by WR (+0.89). "
        "DEF is a modest edge (+0.34). QB is nearly irrelevant as a differentiator (+0.13).\n\n"
        "Kicker is the only position where champions actually average FEWER points than non-champions (-0.75). "
        "Reaching for a kicker is a waste.\n\n"
        "Most striking: the top QB scorer in the league has NEVER won a championship in 23 seasons (0 for 23). "
        "The top RB scorer has won twice (9%). The top WR scorer has won 4 times (17%). "
        "Dominating a single position does not win titles. "
        "Championships come from balanced, above-average production — especially at TE.\n\n"
        "WR accounts for 31.8% of champion scoring, RB 26.8%, QB 17.7%, TE 8.7%, DEF 8.0%, K 7.0%."
    ),
    "tags": "draft,strategy,TE,QB,RB,WR,position,championship,analysis"
}

conn = get_conn()
conn.execute(
    "INSERT OR IGNORE INTO league_lore (season, category, title, content, tags) VALUES (?,?,?,?,?)",
    (LORE["season"], LORE["category"], LORE["title"], LORE["content"], LORE["tags"])
)
conn.commit()
new_id = conn.execute("SELECT MAX(id) FROM league_lore").fetchone()[0]
print(f"Added lore entry [{new_id}]: {LORE['title']}")
conn.close()

# Push to Turso
TURSO_URL   = "https://lsn2k-guerillaradio.aws-us-east-2.turso.io"
TURSO_TOKEN = "eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9.eyJhIjoicnciLCJpYXQiOjE3ODAxNTE2MDksImlkIjoiMDE5ZTc5NDgtYWQwMS03ZmEyLWE4YzYtNDAyZjRkNWU2MTg0IiwicmlkIjoiODBiMjZkODUtOGI2MC00NWQwLWIyYTQtNDFlNmFiYWI0ODcwIn0.Pi0OoD5t8XuZp1Z45PaTX4ntJv3HuCWt0SWptoF9LOTSstbGw0MHa7PuWwK5SUJKCczKN6AC0EI87b3fs2XVAQ"
headers = {"Authorization": f"Bearer {TURSO_TOKEN}", "Content-Type": "application/json"}

escaped = LORE["content"].replace("'", "''")
title_e = LORE["title"].replace("'", "''")
tags_e  = LORE["tags"].replace("'", "''")
sql = f"INSERT OR IGNORE INTO league_lore (id, season, category, title, content, tags) VALUES ({new_id}, NULL, '{LORE['category']}', '{title_e}', '{escaped}', '{tags_e}')"
payload = {"requests": [{"type": "execute", "stmt": {"sql": sql}}, {"type": "close"}]}
resp = requests.post(f"{TURSO_URL}/v2/pipeline", headers=headers, json=payload, timeout=15)
print(f"Turso: {resp.json()['results'][0].get('type')}")
