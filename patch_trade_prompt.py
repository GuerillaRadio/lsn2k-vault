content = open('src/chat.py', encoding='utf-8').read()

lore = """**trade_summary** — PRE-COMPUTED trade analytics. Use this for ANY trade question. One row per trade.
  transaction_key, season, trade_date, trade_week,
  trader_nickname, tradee_nickname,
  trader_gets (JSON list of player names trader received),
  tradee_gets (JSON list of player names tradee received),
  trader_pts_gained (fantasy pts those players scored rest of season),
  tradee_pts_gained (same for tradee),
  point_diff (abs difference — bigger = more lopsided),
  trade_winner (nickname who got the better deal), trade_loser

  For "most lopsided trade": SELECT * FROM trade_summary ORDER BY point_diff DESC LIMIT 1
  For trades by a person: WHERE trader_nickname='X' OR tradee_nickname='X'
  Never manually join transactions + transaction_players for trade questions — use this table.

"""

old = "**league_lore**"
content = content.replace(old, lore + "**league_lore**")
open('src/chat.py', 'w', encoding='utf-8').write(content)
print("done")
