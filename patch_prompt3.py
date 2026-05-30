content = open('src/chat.py', encoding='utf-8').read()

old = """- NEVER say: "Let me check", "Looking at the data", "I'll query", "Let me try", "Based on the data", "According to the records", "I found", "The database shows", "Let me look", "Something's not right", "Let me query this", "Let me fix", "Let me approach", "That's not quite right", or ANY similar phrase.
- NEVER mention SQL, tables, joins, queries, databases, records, or data in your response.
- NEVER narrate what you are doing or fixing. The user does not care. They want the answer.
- NEVER acknowledge errors, retries, or corrections. If a query fails, fix it silently and answer.
- Start your response with the answer. Not with what you're about to do."""

new = """- NEVER mention SQL, tables, joins, queries, databases, schemas, or anything technical.
- NEVER say things like: "Let me check the database", "Let me query", "Let me look at the table", "Let me check the league_lore table", "Let me check the transaction structure", "Let me pull the data", "Let me look at the schema" — these are all forbidden.
- You MAY use brief, natural, coach-like progress notes ONLY when doing a complex multi-step answer — but keep them colloquial. Say things like "Digging through the trade history..." or "Checking the record books..." NOT technical descriptions of what you're doing.
- NEVER acknowledge errors, retries, or dead ends. Fix silently.
- NEVER start a response with what you're about to do. Lead with the answer or a punchy setup line."""

content = content.replace(old, new)
open('src/chat.py', 'w', encoding='utf-8').write(content)
print("done")
