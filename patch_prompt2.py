content = open('src/chat.py', encoding='utf-8').read()
old = "**championships** — THE ONLY authoritative source for championship winners. Always use this table for any question about who won a title. Never derive champions from standings rank or matchup results."
new = """**championships** — THE ONLY authoritative source for championship winners. Always use this table for any question about who won a title. Never derive champions from standings rank or matchup results.
  NOTE: 2022 has TWO entries — Scott Butler AND Nick Gililland are both co-champions (the game ended in an 85.5-85.5 tie). This is NOT a data error. It is correct and intentional. Never call it a duplicate."""
content = content.replace(old, new)
open('src/chat.py', 'w', encoding='utf-8').write(content)
print("done")
