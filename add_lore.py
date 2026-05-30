import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))
from database import get_conn
conn = get_conn()

conn.execute("""
    INSERT OR IGNORE INTO league_lore (season, category, title, content, tags)
    VALUES (NULL, 'story', 'Dusty Gets a Green Slip',
    'Back in high school, Dustin Butler called Coach Taylor a dickhead to his face in front of the whole team. Coach wrote him up on the spot — green slip, sent straight to the principal. Dusty has never lived it down. Coach brings it up whenever Dusty questions him, talks back, or has a bad season. To this day it remains the gold standard green slip in Coach Taylor''s disciplinary career, and he considers it one of his finest moments.',
    'Dusty,green slip,discipline,history')
""")
conn.commit()

r = conn.execute("SELECT id, title, content FROM league_lore WHERE title LIKE '%Green Slip%'").fetchone()
print(f"Added: [{r['id']}] {r['title']}")
print(f"Content: {r['content'][:100]}...")
conn.close()
