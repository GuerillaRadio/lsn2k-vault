content = open('src/chat.py', encoding='utf-8').read()

lore_entry = """**league_lore** — historical stories, rule changes, traditions, rivalries, and milestones curated by the league. Query this when answering questions about league history, notable events, or when adding color to an answer.
  id, season (nullable), category (rule_change/story/rivalry/tradition/milestone/draft_story/other),
  title, content (full text), tags (comma-separated names/keywords)
  Example: SELECT * FROM league_lore WHERE tags LIKE '%Falk%' OR content LIKE '%auction%'

"""

old = "**final_standings**"
content = content.replace(old, lore_entry + "**final_standings**")
open('src/chat.py', 'w', encoding='utf-8').write(content)
print("done")
