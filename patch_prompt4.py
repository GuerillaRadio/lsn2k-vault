content = open('src/chat.py', encoding='utf-8').read()

# Add hallucination rule right after the ABSOLUTELY FORBIDDEN section
old = "- NEVER acknowledge errors, retries, or dead ends. Fix silently."
new = """- NEVER acknowledge errors, retries, or dead ends. Fix silently.
- NEVER, EVER make up or hallucinate data. If a query returns no results, run a different query — do NOT invent player names, trade details, scores, or stories. Every fact must come from a query result.
- If you genuinely cannot find the data after multiple attempts, say "I couldn't find that in the records" — do NOT fabricate an answer."""

content = content.replace(old, new)

# Add trade query guidance to the schema section
old_tx = """**transactions** — every add, drop, trade, waiver claim
  transaction_key (PK), league_key, season, type, status, timestamp,
  faab_bid, trader_team_key, tradee_team_key"""

new_tx = """**transactions** — every add, drop, trade, waiver claim
  transaction_key (PK), league_key, season, type (add/drop/trade/commissioner),
  status (successful = completed), timestamp, faab_bid, trader_team_key, tradee_team_key
  NOTE: There are 253 successful trades in this league's history. To find trades:
  WHERE type='trade' AND status='successful'
  Join transaction_players to see which players were exchanged."""

content = content.replace(old_tx, new_tx)
open('src/chat.py', 'w', encoding='utf-8').write(content)
print("done")
