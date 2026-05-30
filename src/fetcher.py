"""Fetch all available data from Yahoo Fantasy Sports API and store in SQLite."""

import json
import time
import sqlite3
from yahoo_oauth import OAuth2
from database import get_conn

FANTASY_BASE = "https://fantasysports.yahooapis.com/fantasy/v2"
RATE_LIMIT_DELAY = 0.8  # seconds between requests


def _get(oauth: OAuth2, url: str) -> dict:
    time.sleep(RATE_LIMIT_DELAY)
    resp = oauth.session.get(url, params={"format": "json"})
    if resp.status_code == 429:
        print("  Rate limited — waiting 60s...")
        time.sleep(60)
        resp = oauth.session.get(url, params={"format": "json"})
    if resp.status_code == 401:
        # Token expired mid-run — refresh and retry once
        print("  Token expired — refreshing...")
        try:
            oauth.refresh_access_token()
            resp = oauth.session.get(url, params={"format": "json"})
        except Exception as e:
            print(f"  Refresh failed: {e}")
    resp.raise_for_status()
    return resp.json().get("fantasy_content", {})


def _flatten_player_info(raw: list) -> dict:
    """Flatten Yahoo's list-of-dicts player info into a single dict."""
    flat = {}
    for item in raw:
        if isinstance(item, dict):
            flat.update(item)
    return flat


# ---------------------------------------------------------------------------
# Stat categories (game-level, not league-level)
# ---------------------------------------------------------------------------

def fetch_stat_categories(oauth: OAuth2, game_key: str, conn: sqlite3.Connection):
    existing = conn.execute(
        "SELECT 1 FROM stat_categories WHERE game_key=? LIMIT 1", (game_key,)
    ).fetchone()
    if existing:
        return

    data = _get(oauth, f"{FANTASY_BASE}/game/{game_key}/stat_categories")
    game_raw = data.get("game", [{}, {}])
    cats_raw = game_raw[1].get("stat_categories", {}).get("stats", []) if len(game_raw) > 1 else []
    if isinstance(cats_raw, list):
        stat_list = cats_raw
    else:
        stat_list = [cats_raw.get(str(i), {}) for i in range(cats_raw.get("count", 0))]

    for item in stat_list:
        s = item.get("stat", {}) if isinstance(item, dict) else {}
        pos_types = s.get("position_types", [])
        pos_str = ",".join(
            pt.get("position_type", "") for pt in pos_types
            if isinstance(pt, dict)
        ) if isinstance(pos_types, list) else ""
        conn.execute("""
            INSERT OR IGNORE INTO stat_categories
                (game_key, stat_id, name, display_name, sort_order, position_type)
            VALUES (?,?,?,?,?,?)
        """, (
            game_key,
            str(s.get("stat_id", "")),
            s.get("name"),
            s.get("display_name"),
            str(s.get("sort_order", "")),
            pos_str,
        ))
    conn.commit()


# ---------------------------------------------------------------------------
# League info
# ---------------------------------------------------------------------------

def fetch_league(oauth: OAuth2, league_key: str, conn: sqlite3.Connection) -> dict:
    data = _get(oauth, f"{FANTASY_BASE}/league/{league_key}")
    raw = data.get("league", [{}])
    l = raw[0] if isinstance(raw, list) else raw

    conn.execute("""
        INSERT OR REPLACE INTO leagues
            (league_key, season, name, num_teams, scoring_type,
             start_week, end_week, start_date, end_date,
             current_week, is_finished, game_key)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        league_key,
        int(l.get("season", 0)),
        l.get("name"),
        int(l.get("num_teams", 0)),
        l.get("scoring_type"),
        int(l.get("start_week", 1)),
        int(l.get("end_week", 16)),
        l.get("start_date"),
        l.get("end_date"),
        int(l.get("current_week") or 1),
        int(l.get("is_finished", 0)),
        league_key.split(".")[0],
    ))
    conn.commit()
    return l


# ---------------------------------------------------------------------------
# League settings (scoring + roster config)
# ---------------------------------------------------------------------------

def fetch_settings(oauth: OAuth2, league_key: str, conn: sqlite3.Connection):
    data = _get(oauth, f"{FANTASY_BASE}/league/{league_key}/settings")
    raw = data.get("league", [{}, {}])
    settings = raw[1].get("settings", [{}])[0] if isinstance(raw, list) and len(raw) > 1 else {}

    # Update league row with settings fields
    conn.execute("""
        UPDATE leagues SET
            playoff_start_week  = ?,
            num_playoff_teams   = ?,
            waiver_type         = ?,
            waiver_rule         = ?,
            trade_end_date      = ?,
            trade_ratify_type   = ?
        WHERE league_key = ?
    """, (
        settings.get("playoff_start_week"),
        settings.get("num_playoff_teams"),
        settings.get("waiver_type"),
        settings.get("waiver_rule"),
        settings.get("trade_end_date"),
        settings.get("trade_ratify_type"),
        league_key,
    ))

    # Roster positions (Yahoo returns a list)
    roster_pos = settings.get("roster_positions", [])
    if not isinstance(roster_pos, list):
        roster_pos = [roster_pos.get(str(i), {}) for i in range(roster_pos.get("count", 0))]
    for item in roster_pos:
        rp = item.get("roster_position", {}) if isinstance(item, dict) else {}
        if rp.get("position"):
            conn.execute("""
                INSERT OR REPLACE INTO roster_positions
                    (league_key, position, count, position_type)
                VALUES (?,?,?,?)
            """, (
                league_key,
                rp.get("position"),
                int(rp.get("count", 1)),
                rp.get("position_type"),
            ))

    # Scoring settings (Yahoo returns a list)
    stat_mods = settings.get("stat_modifiers", {}).get("stats", [])
    if not isinstance(stat_mods, list):
        scount = stat_mods.get("count", 0)
        stat_mods = [stat_mods.get(str(i), {}) for i in range(scount)]
    for item in stat_mods:
        s = item.get("stat", {}) if isinstance(item, dict) else {}
        if s.get("stat_id") is not None:
            conn.execute("""
                INSERT OR REPLACE INTO scoring_settings
                    (league_key, stat_id, value, bonus_type)
                VALUES (?,?,?,?)
            """, (
                league_key,
                str(s.get("stat_id", "")),
                float(s.get("value", 0)),
                s.get("bonus_type"),
            ))

    conn.commit()


# ---------------------------------------------------------------------------
# Teams
# ---------------------------------------------------------------------------

def fetch_teams(oauth: OAuth2, league_key: str, season: int, conn: sqlite3.Connection) -> int:
    data = _get(oauth, f"{FANTASY_BASE}/league/{league_key}/teams")
    raw = data.get("league", [{}, {}])
    teams_data = raw[1].get("teams", {}) if isinstance(raw, list) and len(raw) > 1 else {}
    count = teams_data.get("count", 0)

    for i in range(count):
        entry = teams_data.get(str(i), {}).get("team", [{}])
        t_info = entry[0] if isinstance(entry, list) else entry
        if isinstance(t_info, list):
            t_info = _flatten_player_info(t_info)
        elif not isinstance(t_info, dict):
            continue

        managers = t_info.get("managers", [])
        if isinstance(managers, list) and managers:
            first = managers[0]
            mgr = first.get("manager", {}) if isinstance(first, dict) else {}
        elif isinstance(managers, dict):
            mgr = managers.get("0", {}).get("manager", {})
        else:
            mgr = {}

        logos = t_info.get("team_logos", [])
        logo_url = None
        if isinstance(logos, list) and logos:
            logo_url = logos[0].get("team_logo", {}).get("url")

        conn.execute("""
            INSERT OR REPLACE INTO teams
                (team_key, league_key, season, team_id, name,
                 manager_name, manager_guid, waiver_priority,
                 draft_grade, draft_recap_url, logo_url, clinched_playoffs)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            t_info.get("team_key", ""),
            league_key, season,
            int(t_info.get("team_id", 0)),
            t_info.get("name"),
            mgr.get("nickname") or mgr.get("manager_id"),
            mgr.get("guid"),
            t_info.get("waiver_priority"),
            t_info.get("draft_grade"),
            t_info.get("draft_recap_url"),
            logo_url,
            int(t_info.get("clinched_playoffs", 0)),
        ))
    conn.commit()
    return count


# ---------------------------------------------------------------------------
# Standings
# ---------------------------------------------------------------------------

def fetch_standings(oauth: OAuth2, league_key: str, season: int, conn: sqlite3.Connection):
    data = _get(oauth, f"{FANTASY_BASE}/league/{league_key}/standings")
    raw = data.get("league", [{}, {}])
    if not isinstance(raw, list) or len(raw) < 2:
        return
    standings_wrapper = raw[1].get("standings", [{}])
    teams_data = standings_wrapper[0].get("teams", {}) if standings_wrapper else {}
    count = teams_data.get("count", 0)

    for i in range(count):
        entry = teams_data.get(str(i), {}).get("team", [{}])
        t_info = entry[0] if isinstance(entry, list) else entry
        if isinstance(t_info, list):
            t_info = _flatten_player_info(t_info)

        # team_standings is at index 2 (index 1 is team_points), fallback to index 1
        stats = {}
        if isinstance(entry, list):
            for idx in [2, 1]:
                if len(entry) > idx and isinstance(entry[idx], dict) and "team_standings" in entry[idx]:
                    stats = entry[idx].get("team_standings", {})
                    break
        outcome = stats.get("outcome_totals", {})
        streak = stats.get("streak", {})

        conn.execute("""
            INSERT OR REPLACE INTO standings
                (team_key, league_key, season, rank, playoff_seed,
                 wins, losses, ties, points_for, points_against,
                 streak_type, streak_length)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            t_info.get("team_key", ""),
            league_key, season,
            int(stats.get("rank", 0)),
            int(stats.get("playoff_seed") or 0),
            int(outcome.get("wins", 0)),
            int(outcome.get("losses", 0)),
            int(outcome.get("ties", 0)),
            float(stats.get("points_for") or 0),
            float(stats.get("points_against") or 0),
            streak.get("type"),
            int(streak.get("value", 0)),
        ))
    conn.commit()


# ---------------------------------------------------------------------------
# Matchups
# ---------------------------------------------------------------------------

def fetch_matchups(oauth: OAuth2, league_key: str, season: int,
                   start_week: int, end_week: int, conn: sqlite3.Connection):
    for week in range(start_week, end_week + 1):
        data = _get(oauth, f"{FANTASY_BASE}/league/{league_key}/scoreboard;week={week}")
        raw = data.get("league", [{}, {}])
        scoreboard = raw[1].get("scoreboard", {}) if isinstance(raw, list) and len(raw) > 1 else {}
        matchups_data = scoreboard.get("0", {}).get("matchups", {})
        if not matchups_data:
            continue
        mcount = matchups_data.get("count", 0)

        for m in range(mcount):
            matchup = matchups_data.get(str(m), {}).get("matchup", {})
            is_playoffs   = int(matchup.get("is_playoffs", 0))
            is_consolation = int(matchup.get("is_consolation", 0))
            is_bye        = int(matchup.get("is_bye_week", 0))
            winner_key    = matchup.get("winner_team_key") or None

            teams_in = matchup.get("0", {}).get("teams", {})
            tcount   = teams_in.get("count", 0)
            keys, pts, proj = [], [], []

            for t in range(tcount):
                te = teams_in.get(str(t), {}).get("team", [{}])
                t_info = te[0]
                if isinstance(t_info, list):
                    t_info = _flatten_player_info(t_info)
                tk  = t_info.get("team_key")
                tp  = te[1].get("team_points", {}).get("total") if len(te) > 1 else None
                tpr = te[1].get("team_projected_points", {}).get("total") if len(te) > 1 else None
                keys.append(tk)
                pts.append(float(tp) if tp is not None else None)
                proj.append(float(tpr) if tpr is not None else None)

            conn.execute("""
                INSERT OR IGNORE INTO matchups
                    (league_key, season, week, team1_key, team2_key,
                     team1_points, team2_points, team1_projected, team2_projected,
                     winner_team_key, is_playoffs, is_consolation, is_bye)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (
                league_key, season, week,
                keys[0] if len(keys) > 0 else None,
                keys[1] if len(keys) > 1 else None,
                pts[0]  if len(pts)  > 0 else None,
                pts[1]  if len(pts)  > 1 else None,
                proj[0] if len(proj) > 0 else None,
                proj[1] if len(proj) > 1 else None,
                winner_key, is_playoffs, is_consolation, is_bye,
            ))
        conn.commit()
        print(f"    Week {week}: {mcount} matchups")


# ---------------------------------------------------------------------------
# Draft
# ---------------------------------------------------------------------------

def fetch_draft(oauth: OAuth2, league_key: str, season: int, conn: sqlite3.Connection) -> list[str]:
    data = _get(oauth, f"{FANTASY_BASE}/league/{league_key}/draftresults")
    raw = data.get("league", [{}, {}])
    draft = raw[1].get("draft_results", {}) if isinstance(raw, list) and len(raw) > 1 else {}
    count = draft.get("count", 0)

    player_keys = []
    for i in range(count):
        pick = draft.get(str(i), {}).get("draft_result", {})
        pk = pick.get("player_key")
        if pk:
            player_keys.append(pk)
        conn.execute("""
            INSERT OR IGNORE INTO draft_picks
                (league_key, season, round, pick, team_key, player_key)
            VALUES (?,?,?,?,?,?)
        """, (
            league_key, season,
            int(pick.get("round", 0)),
            int(pick.get("pick", 0)),
            pick.get("team_key"),
            pk,
        ))
    conn.commit()
    return player_keys


# ---------------------------------------------------------------------------
# Players (batch upsert)
# ---------------------------------------------------------------------------

def fetch_players(oauth: OAuth2, player_keys: list[str], conn: sqlite3.Connection):
    # Only fetch keys not already in DB
    new_keys = [
        k for k in player_keys
        if k and not conn.execute(
            "SELECT 1 FROM players WHERE player_key=?", (k,)
        ).fetchone()
    ]
    for i in range(0, len(new_keys), 25):
        batch = new_keys[i:i + 25]
        data = _get(oauth, f"{FANTASY_BASE}/players;player_keys={','.join(batch)}")
        players = data.get("players", {})
        pcount = players.get("count", 0)
        for j in range(pcount):
            pe = players.get(str(j), {}).get("player", [{}])
            p = _flatten_player_info(pe[0]) if isinstance(pe[0], list) else (pe[0] if isinstance(pe, list) else pe)
            name = p.get("name", {})
            positions = p.get("eligible_positions", [])
            pos_str = ",".join(
                ep.get("position", "") for ep in positions
                if isinstance(ep, dict)
            ) if isinstance(positions, list) else ""

            conn.execute("""
                INSERT OR IGNORE INTO players
                    (player_key, name, first_name, last_name,
                     position, nfl_team, jersey_number, status)
                VALUES (?,?,?,?,?,?,?,?)
            """, (
                p.get("player_key"),
                name.get("full"),
                name.get("first"),
                name.get("last"),
                p.get("primary_position") or pos_str,
                p.get("editorial_team_abbr"),
                p.get("uniform_number"),
                p.get("status"),
            ))
        conn.commit()


# ---------------------------------------------------------------------------
# Rosters + player weekly stats
# ---------------------------------------------------------------------------

def fetch_rosters_and_stats(oauth: OAuth2, league_key: str, season: int,
                             start_week: int, end_week: int, conn: sqlite3.Connection):
    teams = conn.execute(
        "SELECT team_key FROM teams WHERE league_key=?", (league_key,)
    ).fetchall()
    team_keys = [r["team_key"] for r in teams]

    for week in range(start_week, end_week + 1):
        all_player_keys = []

        # ---- Rosters ----
        keys_str = ",".join(team_keys)
        data = _get(oauth, f"{FANTASY_BASE}/teams;team_keys={keys_str}/roster;week={week}")
        teams_data = data.get("teams", {})
        tcount = teams_data.get("count", 0)

        for t in range(tcount):
            team_entry = teams_data.get(str(t), {}).get("team", [{}])
            t_info = team_entry[0]
            if isinstance(t_info, list):
                t_info = _flatten_player_info(t_info)
            tk = t_info.get("team_key", "")

            roster = team_entry[1].get("roster", {}) if len(team_entry) > 1 else {}
            players_data = roster.get("0", {}).get("players", {})
            pcount = players_data.get("count", 0)

            for p in range(pcount):
                pe = players_data.get(str(p), {}).get("player", [{}])
                p_info = _flatten_player_info(pe[0]) if isinstance(pe[0], list) else (pe[0] if isinstance(pe, list) else pe)
                player_key = p_info.get("player_key")
                if not player_key:
                    continue
                all_player_keys.append(player_key)

                # Selected position
                sel_pos = None
                if isinstance(pe, list) and len(pe) > 1 and isinstance(pe[1], dict):
                    sp = pe[1].get("selected_position", [])
                    if isinstance(sp, list):
                        for item in sp:
                            if isinstance(item, dict) and "position" in item:
                                sel_pos = item["position"]
                                break
                    elif isinstance(sp, dict):
                        sel_pos = sp.get("position")

                is_starting = 0 if sel_pos in ("BN", "IR") else 1
                conn.execute("""
                    INSERT OR IGNORE INTO roster_slots
                        (league_key, team_key, season, week,
                         player_key, selected_position, is_starting)
                    VALUES (?,?,?,?,?,?,?)
                """, (league_key, tk, season, week, player_key, sel_pos, is_starting))

        conn.commit()

        # Ensure all players are in the players table
        fetch_players(oauth, list(set(all_player_keys)), conn)

        # ---- Player stats + fantasy points for this week ----
        unique_keys = list(set(all_player_keys))
        for i in range(0, len(unique_keys), 25):
            batch = unique_keys[i:i + 25]
            keys_str2 = ",".join(batch)
            sdata = _get(
                oauth,
                f"{FANTASY_BASE}/league/{league_key}/players;player_keys={keys_str2}"
                f"/stats;type=week;week={week}"
            )
            # Stats endpoint wraps players inside league[1]
            sraw = sdata.get("league", [{}, {}])
            splayers = sraw[1].get("players", {}) if len(sraw) > 1 else sdata.get("players", {})
            spcount = splayers.get("count", 0)

            for j in range(spcount):
                spe = splayers.get(str(j), {}).get("player", [{}])
                sp_info = _flatten_player_info(spe[0]) if isinstance(spe[0], list) else (spe[0] if isinstance(spe, list) else spe)
                pk = sp_info.get("player_key")
                if not pk:
                    continue

                fantasy_pts = None
                stats_dict = {}

                if isinstance(spe, list) and len(spe) > 1:
                    extra = spe[1]
                    if isinstance(extra, dict):
                        # Fantasy points — handle {"0":{...}, "total":"x"} or {"total":"x"}
                        pp = extra.get("player_points", {})
                        if isinstance(pp, dict):
                            fantasy_pts = pp.get("total")
                            if fantasy_pts is not None:
                                fantasy_pts = float(fantasy_pts)

                        # Raw stats — API returns list [{stat:{stat_id,value}}, ...]
                        ps = extra.get("player_stats", {})
                        if isinstance(ps, dict):
                            raw_stats = ps.get("stats", [])
                            # Handle both list and dict-with-count formats
                            if isinstance(raw_stats, dict):
                                raw_stats = [raw_stats.get(str(i), {}) for i in range(raw_stats.get("count", 0))]
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
                """, (
                    league_key, pk, season, week,
                    fantasy_pts,
                    json.dumps(stats_dict) if stats_dict else None,
                ))
            conn.commit()

        print(f"    Week {week}: {tcount} teams, {len(unique_keys)} players")


# ---------------------------------------------------------------------------
# Transactions
# ---------------------------------------------------------------------------

def fetch_transactions(oauth: OAuth2, league_key: str, season: int, conn: sqlite3.Connection):
    total = 0
    start = 0
    batch_size = 25

    while True:
        data = _get(
            oauth,
            f"{FANTASY_BASE}/league/{league_key}/transactions"
            f";types=add,drop,trade,commissioner;count={batch_size};start={start}"
        )
        raw = data.get("league", [{}, {}])
        txs = raw[1].get("transactions", {}) if isinstance(raw, list) and len(raw) > 1 else {}
        if not txs or isinstance(txs, list):
            break
        count = txs.get("count", 0)
        if count == 0:
            break

        for i in range(count):
            tx = txs.get(str(i), {}).get("transaction", [{}])
            tx_info = tx[0] if isinstance(tx, list) else tx
            if isinstance(tx_info, list):
                tx_info = _flatten_player_info(tx_info)

            tx_key    = tx_info.get("transaction_key", "")
            tx_type   = tx_info.get("type")
            tx_status = tx_info.get("status")
            tx_time   = tx_info.get("timestamp")
            faab      = tx_info.get("faab_bid_amount")

            trader_key  = None
            tradee_key  = None
            if tx_type == "trade":
                trader_key = tx_info.get("trader_team_key")
                tradee_key = tx_info.get("tradee_team_key")

            conn.execute("""
                INSERT OR IGNORE INTO transactions
                    (transaction_key, league_key, season, type, status,
                     timestamp, faab_bid, trader_team_key, tradee_team_key)
                VALUES (?,?,?,?,?,?,?,?,?)
            """, (
                tx_key, league_key, season,
                tx_type, tx_status,
                int(tx_time) if tx_time else None,
                int(faab) if faab else None,
                trader_key, tradee_key,
            ))

            # Players involved in the transaction
            players_data = tx[1].get("players", {}) if isinstance(tx, list) and len(tx) > 1 else {}
            if isinstance(players_data, dict):
                pcount = players_data.get("count", 0)
                for j in range(pcount):
                    tp = players_data.get(str(j), {}).get("player", [{}])
                    tp_info = _flatten_player_info(tp[0]) if isinstance(tp[0], list) else (tp[0] if isinstance(tp, list) else tp)

                    player_key = tp_info.get("player_key")
                    name_info  = tp_info.get("name", {})

                    tx_data = {}
                    if isinstance(tp, list) and len(tp) > 1 and isinstance(tp[1], dict):
                        tx_data = tp[1].get("transaction_data", {})
                        if isinstance(tx_data, list) and tx_data:
                            tx_data = tx_data[0]

                    conn.execute("""
                        INSERT OR IGNORE INTO transaction_players
                            (transaction_key, player_key, player_name, position, nfl_team,
                             transaction_type, source_team_key, dest_team_key,
                             source_type, dest_type)
                        VALUES (?,?,?,?,?,?,?,?,?,?)
                    """, (
                        tx_key,
                        player_key,
                        name_info.get("full") if isinstance(name_info, dict) else None,
                        tp_info.get("primary_position"),
                        tp_info.get("editorial_team_abbr"),
                        tx_data.get("type"),
                        tx_data.get("source_team_key"),
                        tx_data.get("destination_team_key"),
                        tx_data.get("source_type"),
                        tx_data.get("destination_type"),
                    ))

        conn.commit()
        total += count
        if count < batch_size:
            break
        start += batch_size

    print(f"    {total} transactions")
    return total


# ---------------------------------------------------------------------------
# Full season fetch
# ---------------------------------------------------------------------------

def fetch_season(league_key: str, season: int):
    # Create a fresh OAuth2 object each season so yahoo_oauth auto-refreshes expired tokens
    from auth import get_oauth
    oauth = get_oauth()
    conn = get_conn()
    print(f"\n--- {season} ({league_key}) ---")
    game_key = league_key.split(".")[0]

    print("  Stat categories...")
    try:
        fetch_stat_categories(oauth, game_key, conn)
    except Exception as e:
        print(f"    Skipped: {e}")

    print("  League info...")
    l = fetch_league(oauth, league_key, conn)
    start_week  = int(l.get("start_week", 1))
    end_week    = int(l.get("end_week", 16))
    is_finished = int(l.get("is_finished", 0))
    current_week = int(l.get("current_week") or end_week)
    last_week   = end_week if is_finished else max(1, current_week - 1)

    print("  League settings...")
    try:
        fetch_settings(oauth, league_key, conn)
    except Exception as e:
        print(f"    Skipped: {e}")

    print("  Teams...")
    fetch_teams(oauth, league_key, season, conn)

    print("  Standings...")
    fetch_standings(oauth, league_key, season, conn)

    print("  Draft results...")
    player_keys = fetch_draft(oauth, league_key, season, conn)
    if player_keys:
        fetch_players(oauth, player_keys, conn)

    print(f"  Matchups (weeks 1-{last_week})...")
    fetch_matchups(oauth, league_key, season, start_week, last_week, conn)

    if last_week >= start_week:
        print(f"  Rosters + stats (weeks 1-{last_week})...")
        fetch_rosters_and_stats(oauth, league_key, season, start_week, last_week, conn)

    print("  Transactions...")
    try:
        fetch_transactions(oauth, league_key, season, conn)
    except Exception as e:
        print(f"    Skipped: {e}")

    conn.close()
    print(f"  Done.")
