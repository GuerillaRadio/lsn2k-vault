import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))
from database import get_conn

conn = get_conn()

print("=== TEAM COUNTS PER SEASON ===")
for r in conn.execute("SELECT season, COUNT(*) as n FROM teams GROUP BY season ORDER BY season").fetchall():
    flag = " <-- WRONG" if r["n"] not in (10, 12) else ""
    print(f"  {r['season']}: {r['n']} teams{flag}")

print("\n=== MATCHUP COUNTS PER SEASON ===")
for r in conn.execute("SELECT season, COUNT(*) as total, SUM(is_playoffs) as playoffs, SUM(is_bye) as byes FROM matchups GROUP BY season ORDER BY season").fetchall():
    print(f"  {r['season']}: {r['total']} total, {r['playoffs']} playoff, {r['byes']} bye")

print("\n=== MISSING CHAMPIONSHIPS ===")
all_seasons = [r[0] for r in conn.execute("SELECT DISTINCT season FROM leagues ORDER BY season").fetchall()]
champ_seasons = [r[0] for r in conn.execute("SELECT DISTINCT season FROM championships").fetchall()]
missing = [s for s in all_seasons if s not in champ_seasons]
print(f"  Missing: {missing if missing else 'none'}")

print("\n=== CHAMPIONSHIP ROLL ===")
for r in conn.execute("SELECT c.season, o.nickname, c.note FROM championships c JOIN owners o ON c.owner_id=o.owner_id ORDER BY c.season").fetchall():
    note = f" ({r['note']})" if r["note"] else ""
    print(f"  {r['season']}: {r['nickname']}{note}")

print("\n=== UNMAPPED TEAMS ===")
rows = conn.execute("""
    SELECT t.season, t.name, t.manager_name
    FROM teams t LEFT JOIN team_owner_map m ON t.team_key=m.team_key
    WHERE m.owner_id IS NULL ORDER BY t.season
""").fetchall()
print(f"  {len(rows)} unmapped teams")
for r in rows:
    print(f"    {r['season']}: {r['name']} ({r['manager_name']})")

print("\n=== HIGHEST SCORES SANITY CHECK ===")
for r in conn.execute("""
    SELECT w.season, w.week, o.nickname, w.score
    FROM weekly_high_scores w JOIN owners o ON w.owner_id=o.owner_id
    ORDER BY w.score DESC LIMIT 10
""").fetchall():
    print(f"  {r['season']} wk{r['week']}: {r['nickname']} {r['score']}")

print("\n=== SEASONS WITH NO TRANSACTION DATA ===")
for r in conn.execute("SELECT season, COUNT(*) as n FROM transactions GROUP BY season ORDER BY season").fetchall():
    if r["n"] == 0:
        print(f"  {r['season']}: no transactions")
print("  (checking all...)")
for s in all_seasons:
    n = conn.execute("SELECT COUNT(*) FROM transactions WHERE season=?", (s,)).fetchone()[0]
    if n == 0:
        print(f"  {s}: ZERO transactions")

print("\n=== POINTS TOTALS PER SEASON (sanity) ===")
for r in conn.execute("""
    SELECT season, ROUND(SUM(team1_points),0) as total_pts, COUNT(*) as games
    FROM matchups WHERE is_bye=0 GROUP BY season ORDER BY season
""").fetchall():
    avg = r["total_pts"] / r["games"] / 2 if r["games"] else 0
    flag = " <-- LOW?" if avg < 60 else ""
    print(f"  {r['season']}: avg score {avg:.1f} pts/team/game{flag}")

conn.close()
