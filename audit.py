import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))
from database import get_conn

conn = get_conn()

early = [2004, 2005, 2006, 2007, 2009]
tables = [
    ("standings (rank>0)",  "SELECT COUNT(*) FROM standings WHERE season=? AND rank>0"),
    ("matchups",            "SELECT COUNT(*) FROM matchups WHERE season=?"),
    ("draft_picks",         "SELECT COUNT(*) FROM draft_picks WHERE season=?"),
    ("roster_slots",        "SELECT COUNT(*) FROM roster_slots WHERE season=?"),
    ("player_stats w/pts",  "SELECT COUNT(*) FROM player_weekly_stats WHERE season=? AND fantasy_points IS NOT NULL"),
    ("transactions",        "SELECT COUNT(*) FROM transactions WHERE season=?"),
    ("scoring_settings",    "SELECT COUNT(*) FROM scoring_settings WHERE league_key IN (SELECT league_key FROM leagues WHERE season=?)"),
]

header = f"{'Table':<25}" + "".join(f"{s:>7}" for s in early)
print(header)
print("-" * (25 + 7 * len(early)))
for label, sql in tables:
    row = f"{label:<25}"
    for s in early:
        n = conn.execute(sql, (s,)).fetchone()[0]
        row += f"{n:>7}"
    print(row)

# Also compare to a known-good recent season
print()
print("For comparison, 2023:")
for label, sql in tables:
    n = conn.execute(sql.replace("season=?", "season=2023").replace("WHERE season=?", "WHERE season=2023"), ()).fetchone()[0]
    print(f"  {label:<25} {n}")

conn.close()
