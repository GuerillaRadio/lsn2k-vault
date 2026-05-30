import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))
from database import get_conn
conn = get_conn()

# Fix 2025 champion — matchup data clearly shows Utz beat T-Bone 93.87 vs 71.53
conn.execute("DELETE FROM championships WHERE season=2025")
utz_id = conn.execute("SELECT owner_id FROM owners WHERE nickname='Utz'").fetchone()["owner_id"]
conn.execute("INSERT INTO championships (season, owner_id) VALUES (?,?)", (2025, utz_id))
conn.commit()
print("Fixed 2025: now Utz")

# Verify all championships match the actual final-week game results
print("\nChecking all championships vs matchup results:")
games = conn.execute("""
    SELECT m.season, o1.nickname as t1, o2.nickname as t2,
           ow.nickname as winner, oc.nickname as recorded_champ, c.note
    FROM matchups m
    JOIN team_owner_map map1 ON m.team1_key=map1.team_key
    JOIN owners o1 ON map1.owner_id=o1.owner_id
    JOIN team_owner_map map2 ON m.team2_key=map2.team_key
    JOIN owners o2 ON map2.owner_id=o2.owner_id
    JOIN team_owner_map mapw ON m.winner_team_key=mapw.team_key
    JOIN owners ow ON mapw.owner_id=ow.owner_id
    JOIN leagues l ON m.league_key=l.league_key
    LEFT JOIN championships c ON c.season=m.season
    LEFT JOIN owners oc ON c.owner_id=oc.owner_id
    WHERE m.is_playoffs=1 AND m.is_consolation=0 AND m.week=l.end_week
    ORDER BY m.season
""").fetchall()

for r in games:
    match = "OK" if r["winner"] == r["recorded_champ"] or r["note"] else "MISMATCH"
    note = f" (note: {r['note']})" if r["note"] else ""
    flag = " <-- !!!" if match == "MISMATCH" else ""
    print(f"  {r['season']}: {r['winner']} won — recorded: {r['recorded_champ']}{note}{flag}")

conn.close()
