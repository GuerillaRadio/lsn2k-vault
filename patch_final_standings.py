content = open('src/chat.py', encoding='utf-8').read()

old = """**final_standings** — DEFINITIVE post-playoff rank for every owner every season. Use this first for any question about final standings, finishing position, top-N finishes, or end-of-season results. Never recalculate from matchups.
  owner_id, season, final_rank (1=champion 2=runner-up 3=3rd ... 12=last),
  playoff_result ("champion","runner-up","3rd place","missed playoffs" etc.),
  reg_season_rank, reg_wins, reg_losses, reg_points_for, made_playoffs"""

new = """**final_standings** — DEFINITIVE post-playoff rank for every owner every season. One row per owner per season, no duplicates.
  owner_id, season, final_rank (1=champion 2=runner-up 3=3rd ... 12=last),
  playoff_result ("champion","runner-up","3rd place","missed playoffs" etc.),
  reg_season_rank, reg_wins, reg_losses, reg_points_for, made_playoffs

  For "how many times did X finish top-4":
  SELECT COUNT(*), MIN(final_rank) FROM final_standings fs
  JOIN owners o ON fs.owner_id=o.owner_id
  WHERE o.nickname='X' AND fs.final_rank <= 4
  This is a single query. Do NOT join matchups or standings manually. Do NOT say "join issue"."""

content = content.replace(old, new)
open('src/chat.py', 'w', encoding='utf-8').write(content)
print("done")
