content = open('src/chat.py', encoding='utf-8').read()

new_tables = """## Pre-computed Analytics Tables (always query these first — never recalculate manually)

**matchup_results** — Every game, one row per team. Use for ALL record/score/streak questions.
  season, week, owner_id, nickname, franchise_name, opponent_id, opponent_nickname,
  team_points, opponent_points, won, lost, tied, point_diff,
  is_playoffs, is_consolation, is_regular_season
  WHERE is_regular_season=1 AND is_consolation=0 for regular season records.

**owner_playoff_stats** — Playoff-specific career stats per owner.
  nickname, playoff_appearances, playoff_wins, playoff_losses, playoff_win_pct,
  championship_appearances, championships, runner_up, best_playoff_finish, avg_playoff_finish

**waiver_summary** — Every waiver/free agent pickup with season scoring context.
  season, pickup_week, pickup_date, nickname, player_name, position,
  pts_before (pts before pickup), pts_after (pts rest of season), pts_total, weeks_rostered
  Best pickup: ORDER BY pts_after DESC

**bench_points** — Points started vs benched per owner per week.
  season, week, nickname, pts_started, pts_benched, pts_left_on_bench
  Season total bench waste: SUM(pts_left_on_bench) GROUP BY season, owner_id

**draft_pick_value** — Every draft pick with season fantasy points and value vs expectation.
  season, round, pick, overall_pick, nickname, player_name, position,
  season_pts, avg_pts_at_pick, value_over_avg (positive=steal, negative=bust), was_starter
  Best steals: ORDER BY value_over_avg DESC

**owner_streaks** — Pre-computed win/loss streaks (regular season only, 3+ games).
  nickname, streak_type (win/loss), length, start_season, start_week,
  end_season, end_week, is_current
  Longest ever: ORDER BY length DESC

**season_awards** — Per-season superlatives, all pre-computed.
  season, most_pts_owner, most_pts_value, least_pts_owner, best_record_owner, worst_record_owner,
  highest_week_owner, highest_week_score, highest_week_week,
  biggest_blowout_winner, biggest_blowout_margin, closest_game_margin,
  most_bench_pts_owner, most_trades_owner, champion, runner_up

**owner_vs_owner** — Season-by-season head-to-head breakdowns (more detail than owner_h2h).
  owner_id, opponent_id, season, wins, losses, ties, pts_for, pts_against
  Full rivalry history: WHERE owner_id=X AND opponent_id=Y ORDER BY season

"""

old = "## Pre-computed Aggregate Tables"
content = content.replace(old, new_tables + "## Pre-computed Aggregate Tables (LEGACY — prefer tables above)")
open('src/chat.py', 'w', encoding='utf-8').write(content)
print("done")
