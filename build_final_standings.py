"""
Build final_standings table — one row per owner per season with definitive post-playoff rank.
Ranks 1-2: from championship game
Ranks 3-4: 3rd place game (semi losers from championship bracket)
Ranks 5-8: consolation bracket results
Ranks 9-12: non-playoff teams ordered by regular season rank
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))
from database import get_conn

conn = get_conn()

def _is_winner(m, oid):
    wk = m["winner_team_key"]
    return (m["o1_id"] == oid and wk == m["team1_key"]) or \
           (m["o2_id"] == oid and wk == m["team2_key"])

# Create table
conn.execute("DROP TABLE IF EXISTS final_standings")
conn.executescript("""
    CREATE TABLE final_standings (
        owner_id            INTEGER NOT NULL,
        season              INTEGER NOT NULL,
        final_rank          INTEGER NOT NULL,
        playoff_result      TEXT,
        reg_season_rank     INTEGER,
        reg_wins            INTEGER,
        reg_losses          INTEGER,
        reg_points_for      REAL,
        made_playoffs       INTEGER DEFAULT 0,
        PRIMARY KEY (owner_id, season)
    );
""")
conn.commit()

seasons = conn.execute("SELECT season, league_key, end_week FROM leagues ORDER BY season").fetchall()

for row in seasons:
    season = row["season"]
    league_key = row["league_key"]
    end_week = row["end_week"]

    # Get all playoff matchups sorted by week
    matchups = conn.execute("""
        SELECT m.week, m.team1_key, m.team2_key, m.winner_team_key,
               m.is_consolation,
               map1.owner_id as o1_id, map2.owner_id as o2_id
        FROM matchups m
        JOIN team_owner_map map1 ON m.team1_key=map1.team_key
        JOIN team_owner_map map2 ON m.team2_key=map2.team_key
        WHERE m.league_key=? AND m.is_playoffs=1 AND m.is_bye=0
          AND m.winner_team_key IS NOT NULL
        ORDER BY m.week
    """, (league_key,)).fetchall()

    if not matchups:
        continue

    playoff_weeks = sorted(set(m["week"] for m in matchups))
    if len(playoff_weeks) < 2:
        continue

    end_w = max(playoff_weeks)
    semi_w = playoff_weeks[-2]

    ranks = {}

    # ── Rank 1 & 2: Championship game ─────────────────────────────────────
    champ_game = next(
        (m for m in matchups if m["week"] == end_w and m["is_consolation"] == 0),
        None
    )
    if champ_game:
        winner_oid = champ_game["o1_id"] if _is_winner(champ_game, champ_game["o1_id"]) else champ_game["o2_id"]
        loser_oid  = champ_game["o2_id"] if winner_oid == champ_game["o1_id"] else champ_game["o1_id"]
        ranks[winner_oid] = (1, "champion")
        ranks[loser_oid]  = (2, "runner-up")

    # ── Find 3rd place finalists: lost is_consolation=0 game in semi week ─
    third_place_teams = set()
    for m in matchups:
        if m["week"] == semi_w and m["is_consolation"] == 0:
            loser_oid = m["o2_id"] if _is_winner(m, m["o1_id"]) else m["o1_id"]
            third_place_teams.add(loser_oid)

    # ── Rank 3 & 4: 3rd place game (final week consolation involving 3rd place teams) ─
    for m in [x for x in matchups if x["week"] == end_w and x["is_consolation"] == 1]:
        both_in_3rd = m["o1_id"] in third_place_teams and m["o2_id"] in third_place_teams
        if both_in_3rd:
            winner_oid = m["o1_id"] if _is_winner(m, m["o1_id"]) else m["o2_id"]
            loser_oid  = m["o2_id"] if winner_oid == m["o1_id"] else m["o1_id"]
            if winner_oid not in ranks:
                ranks[winner_oid] = (3, "3rd place")
            if loser_oid not in ranks:
                ranks[loser_oid]  = (4, "4th place")

    # ── Ranks 5-8: remaining final-week consolation games ─────────────────
    consolation_rank = 5
    for m in [x for x in matchups if x["week"] == end_w and x["is_consolation"] == 1]:
        o1, o2 = m["o1_id"], m["o2_id"]
        if o1 not in ranks and o2 not in ranks:
            winner_oid = o1 if _is_winner(m, o1) else o2
            loser_oid  = o2 if winner_oid == o1 else o1
            ranks[winner_oid] = (consolation_rank,     f"{consolation_rank}th place")
            ranks[loser_oid]  = (consolation_rank + 1, f"{consolation_rank+1}th place")
            consolation_rank += 2

    # ── Get regular season data from standings ────────────────────────────
    reg_data = {}
    for s in conn.execute("""
        SELECT tm.owner_id, st.rank, st.wins, st.losses, st.points_for
        FROM standings st
        JOIN team_owner_map tm ON st.team_key=tm.team_key
        WHERE st.league_key=?
    """, (league_key,)).fetchall():
        reg_data[s["owner_id"]] = s

    # ── Ranks 9-12: non-playoff teams by regular season rank ──────────────
    playoff_owner_ids = set(ranks.keys())
    non_playoff = [(oid, reg_data.get(oid)) for oid in reg_data if oid not in playoff_owner_ids]
    non_playoff.sort(key=lambda x: x[1]["rank"] if x[1] and x[1]["rank"] else 99)
    for i, (oid, _) in enumerate(non_playoff):
        ranks[oid] = (9 + i, "missed playoffs")

    # ── Insert into final_standings ───────────────────────────────────────
    for oid, (rank, result) in ranks.items():
        rd = reg_data.get(oid)
        conn.execute("""
            INSERT OR REPLACE INTO final_standings
                (owner_id, season, final_rank, playoff_result,
                 reg_season_rank, reg_wins, reg_losses, reg_points_for, made_playoffs)
            VALUES (?,?,?,?,?,?,?,?,?)
        """, (
            oid, season, rank, result,
            rd["rank"] if rd else None,
            rd["wins"] if rd else None,
            rd["losses"] if rd else None,
            rd["points_for"] if rd else None,
            1 if rank <= 8 else 0,
        ))

conn.commit()

# Report
print("Final standings sample (2023):")
for r in conn.execute("""
    SELECT fs.final_rank, o.nickname, fs.playoff_result, fs.reg_wins, fs.reg_losses
    FROM final_standings fs JOIN owners o ON fs.owner_id=o.owner_id
    WHERE fs.season=2023 ORDER BY fs.final_rank
""").fetchall():
    print(f"  {r['final_rank']:>2}. {r['nickname']:<12} {r['playoff_result']:<20} RS: {r['reg_wins']}-{r['reg_losses']}")

print(f"\nTotal rows: {conn.execute('SELECT COUNT(*) FROM final_standings').fetchone()[0]}")
conn.close()
