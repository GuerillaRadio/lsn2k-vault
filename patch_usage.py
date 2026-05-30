content = open('src/chat.py', encoding='utf-8').read()

# Add usage tracking after the stream completes
old = """    # Save to response cache (single-turn questions only)
    if original_question and len(messages) <= 2 and full_text_blocks:"""

new = """    # Log token usage
    try:
        from database import get_conn as _get_conn
        _conn = _get_conn()
        _conn.execute("""
new += '"""CREATE TABLE IF NOT EXISTS usage_log ('
new += """
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            model TEXT, input_tokens INTEGER, output_tokens INTEGER,
            cache_read_tokens INTEGER, cost_usd REAL,
            asked_at INTEGER DEFAULT (strftime('%s','now'))
        )"""
new += '"""'
new += """)
        _conn.commit()
        _conn.close()
    except Exception:
        pass

    # Save to response cache (single-turn questions only)
    if original_question and len(messages) <= 2 and full_text_blocks:"""

content = content.replace(old, new)
open('src/chat.py', 'w', encoding='utf-8').write(content)
print("done")
