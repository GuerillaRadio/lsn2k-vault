import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))
from database import get_conn

conn = get_conn()
issues = []

seasons = [r["season"] for r in conn.execute("SELECT season FROM leagues ORDER BY season").fetchall()]

print("=== TRANSACTIONS ===")
for s in seasons:
    n = conn.execute("SELECT COUNT(*) FROM transactions WHERE season=?", (s,)).fetchone()[0]
    flag = " <-- ZERO" if n == 0 else (" <-- LOW?" if n < 50 else "")
    print(f"  {s}: {n}{flag}")
    if n == 0:
        issues.append(f"2{s}: zero transactions")

print("\n=== DRAFT PICKS ===")
for s in seasons:
    n = conn.execute("SELECT COUNT(*) FROM draft_picks WHERE season=?", (s,)).fetchone()[0]
    teams = conn.execute("SELECT COUNT(*) FROM teams WHERE season=?", (s,)).fetchone()[0]
    expected = teams * 15  # ~15 rounds
    flag = " <-- ZERO" if n == 0 else (" <-- LOW?" if n < expected * 0.5 else "")
    print(f"  {s}: {n} picks, {teams} teams{flag}")
    if n == 0:
        issues.append(f"{s}: zero draft picks")

print("\n=== ROSTER SLOTS ===")
for s in seasons:
    n = conn.execute("SELECT COUNT(*) FROM roster_slots WHERE season=?", (s,)).fetchone()[0]
    flag = " <-- ZERO" if n == 0 else (" <-- LOW?" if n < 500 else "")
    print(f"  {s}: {n}{flag}")
    if n == 0:
        issues.append(f"{s}: zero roster slots")

print("\n=== PLAYER STATS WITH POINTS ===")
for s in seasons:
    total = conn.execute("SELECT COUNT(*) FROM player_weekly_stats WHERE season=?", (s,)).fetchone()[0]
    with_pts = conn.execute("SELECT COUNT(*) FROM player_weekly_stats WHERE season=? AND fantasy_points IS NOT NULL AND fantasy_points > 0", (s,)).fetchone()[0]
    pct = with_pts/total*100 if total else 0
    flag = " <-- ZERO" if total == 0 else (" <-- LOW?" if pct < 50 else "")
    print(f"  {s}: {with_pts}/{total} have points ({pct:.0f}%){flag}")
    if total == 0:
        issues.append(f"{s}: zero player stats")
    if total > 0 and pct < 50:
        issues.append(f"{s}: only {pct:.0f}% of stats have fantasy points")

print("\n=== OWNER MAPPINGS ===")
unmapped = conn.execute("""
    SELECT t.season, t.name, t.manager_name
    FROM teams t LEFT JOIN team_owner_map m ON t.team_key=m.team_key
    WHERE m.owner_id IS NULL ORDER BY t.season
""").fetchall()
if unmapped:
    for r in unmapped:
        print(f"  {r['season']}: {r['name']} ({r['manager_name']}) -- NO OWNER")
        issues.append(f"{r['season']}: team '{r['name']}' has no owner mapping")
else:
    print("  All teams mapped.")

print("\n=== STANDINGS COMPLETENESS ===")
for s in seasons:
    total_teams = conn.execute("SELECT COUNT(*) FROM teams WHERE season=?", (s,)).fetchone()[0]
    with_rank = conn.execute("SELECT COUNT(*) FROM standings WHERE season=? AND rank > 0", (s,)).fetchone()[0]
    with_wins = conn.execute("SELECT COUNT(*) FROM standings WHERE season=? AND wins > 0", (s,)).fetchone()[0]
    flag = ""
    if with_rank == 0: flag = " <-- NO RANKS"
    elif with_wins == 0: flag = " <-- NO WINS"
    print(f"  {s}: {with_rank}/{total_teams} ranked, {with_wins}/{total_teams} have wins{flag}")
    if with_rank == 0:
        issues.append(f"{s}: standings have no ranks")
    if with_wins == 0:
        issues.append(f"{s}: standings have no wins data")

print("\n=== CONSOLATION FLAG CHECK ===")
for s in seasons:
    total_playoff = conn.execute("SELECT COUNT(*) FROM matchups WHERE season=? AND is_playoffs=1", (s,)).fetchone()[0]
    consolation = conn.execute("SELECT COUNT(*) FROM matchups WHERE season=? AND is_consolation=1", (s,)).fetchone()[0]
    real = total_playoff - consolation
    print(f"  {s}: {real} real playoff, {consolation} consolation (of {total_playoff} total)")

print("\n=== SCORING SETTINGS ===")
for s in seasons:
    n = conn.execute("SELECT COUNT(*) FROM scoring_settings WHERE league_key=(SELECT league_key FROM leagues WHERE season=?)", (s,)).fetchone()[0]
    flag = " <-- ZERO" if n == 0 else ""
    print(f"  {s}: {n} scoring rules{flag}")
    if n == 0:
        issues.append(f"{s}: zero scoring settings")

print("\n=== CHAMPIONSHIP TABLE ===")
champ_seasons = [r[0] for r in conn.execute("SELECT DISTINCT season FROM championships ORDER BY season").fetchall()]
missing = [s for s in seasons if s not in champ_seasons and s != 2026]
if missing:
    print(f"  Missing champions for: {missing}")
    issues.append(f"Missing champions: {missing}")
else:
    print("  All seasons have champion recorded.")

print(f"\n{'='*50}")
print(f"SUMMARY: {len(issues)} issues found")
for i in issues:
    print(f"  - {i}")

conn.close()
