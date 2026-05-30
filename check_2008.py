import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))
from database import get_conn

conn = get_conn()

print("2008 owner_season_stats:")
for r in conn.execute("""
    SELECT o.nickname, oss.wins, oss.losses, oss.points_for, oss.made_playoffs
    FROM owner_season_stats oss JOIN owners o ON oss.owner_id=o.owner_id
    WHERE oss.season=2008 ORDER BY oss.wins DESC
""").fetchall():
    print(f"  {r['nickname']}: {r['wins']}W-{r['losses']}L, {r['points_for']} pts, playoffs={r['made_playoffs']}")

print("\nWeeks in 2008 (regular season):")
for r in conn.execute("""
    SELECT week, COUNT(*) as n FROM matchups
    WHERE season=2008 AND is_playoffs=0
    GROUP BY week ORDER BY week
""").fetchall():
    print(f"  Week {r['week']}: {r['n']} games")

print("\n2008 league settings:")
r = conn.execute("SELECT end_week, playoff_start_week, num_playoff_teams FROM leagues WHERE season=2008").fetchone()
print(f"  end_week={r['end_week']}, playoff_start_week={r['playoff_start_week']}, num_playoff_teams={r['num_playoff_teams']}")

print("\nDraft picks count:", conn.execute("SELECT COUNT(*) FROM draft_picks WHERE season=2008").fetchone()[0])
print("Transactions count:", conn.execute("SELECT COUNT(*) FROM transactions WHERE season=2008").fetchone()[0])

conn.close()
