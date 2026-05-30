"""Re-fetch player weekly stats for all seasons (fixes empty stats_json)."""
import sys, json, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))
from database import get_conn
from auth import get_oauth
from fetcher import _get, fetch_players, FANTASY_BASE, RATE_LIMIT_DELAY

oauth = get_oauth()

conn = get_conn()
seasons = conn.execute("SELECT season, league_key, start_week, end_week, is_finished FROM leagues ORDER BY season").fetchall()

for row in seasons:
    season = row["season"]
    league_key = row["league_key"]
    end_week = row["end_week"] if row["is_finished"] else row["end_week"] - 1
    if end_week < 1:
        continue

    print(f"\n{season} ({league_key})...")

    for week in range(row["start_week"], end_week + 1):
        # Get all player keys on rosters this week
        player_keys = [r["player_key"] for r in conn.execute(
            "SELECT DISTINCT player_key FROM roster_slots WHERE league_key=? AND week=?",
            (league_key, week)
        ).fetchall()]

        if not player_keys:
            continue

        # Fetch in batches of 25
        for i in range(0, len(player_keys), 25):
            batch = player_keys[i:i+25]
            keys_str = ",".join(batch)
            try:
                sdata = _get(oauth, f"{FANTASY_BASE}/league/{league_key}/players;player_keys={keys_str}/stats;type=week;week={week}")
                sraw = sdata.get("league", [{}, {}])
                splayers = sraw[1].get("players", {}) if len(sraw) > 1 else {}
                spcount = splayers.get("count", 0)

                for j in range(spcount):
                    spe = splayers.get(str(j), {}).get("player", [{}])
                    p_info = spe[0] if isinstance(spe, list) else spe
                    if isinstance(p_info, list):
                        flat = {}
                        for d in p_info:
                            if isinstance(d, dict): flat.update(d)
                        p_info = flat
                    pk = p_info.get("player_key")
                    if not pk:
                        continue

                    fantasy_pts = None
                    stats_dict = {}

                    if isinstance(spe, list) and len(spe) > 1 and isinstance(spe[1], dict):
                        extra = spe[1]
                        pp = extra.get("player_points", {})
                        if isinstance(pp, dict):
                            t = pp.get("total")
                            if t is not None:
                                fantasy_pts = float(t)
                        ps = extra.get("player_stats", {})
                        if isinstance(ps, dict):
                            raw_stats = ps.get("stats", [])
                            if isinstance(raw_stats, dict):
                                raw_stats = [raw_stats.get(str(x), {}) for x in range(raw_stats.get("count", 0))]
                            for item in raw_stats:
                                stat = item.get("stat", {}) if isinstance(item, dict) else {}
                                sid = str(stat.get("stat_id", ""))
                                val = stat.get("value")
                                if sid and val is not None and val != "0":
                                    stats_dict[sid] = val

                    conn.execute("""
                        INSERT OR REPLACE INTO player_weekly_stats
                            (league_key, player_key, season, week, fantasy_points, stats_json)
                        VALUES (?,?,?,?,?,?)
                    """, (league_key, pk, season, week, fantasy_pts,
                          json.dumps(stats_dict) if stats_dict else None))

                conn.commit()
            except Exception as e:
                print(f"  Week {week} batch {i//25}: {e}")

        print(f"  Week {week}: {len(player_keys)} players", end="\r")

    print(f"  {season} done.          ")

# Quick check
total = conn.execute("SELECT COUNT(*) FROM player_weekly_stats WHERE stats_json IS NOT NULL AND stats_json != '{}'").fetchone()[0]
print(f"\nTotal rows with stats_json: {total:,}")
conn.close()
