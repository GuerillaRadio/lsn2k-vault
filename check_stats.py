import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))
from database import get_conn
conn = get_conn()

print("Roster slots and stats by season:")
print(f"{'Season':<8} {'Rosters':>10} {'Stats':>10} {'Stats w/pts':>12} {'Stats w/json':>14}")
print("-" * 58)
for s in range(2004, 2027):
    r = conn.execute("SELECT COUNT(*) FROM roster_slots WHERE season=?", (s,)).fetchone()[0]
    t = conn.execute("SELECT COUNT(*) FROM player_weekly_stats WHERE season=?", (s,)).fetchone()[0]
    p = conn.execute("SELECT COUNT(*) FROM player_weekly_stats WHERE season=? AND fantasy_points IS NOT NULL AND fantasy_points > 0", (s,)).fetchone()[0]
    j = conn.execute("SELECT COUNT(*) FROM player_weekly_stats WHERE season=? AND stats_json IS NOT NULL AND stats_json != '{}'", (s,)).fetchone()[0]
    flag = " <--" if (r == 0 or t == 0 or j == 0) else ""
    print(f"  {s:<6} {r:>10,} {t:>10,} {p:>12,} {j:>14,}{flag}")

conn.close()
