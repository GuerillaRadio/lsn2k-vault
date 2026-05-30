content = open('app.py', encoding='utf-8').read()

old = '''@app.route("/recent")
def recent():
    from database import get_conn
    conn = get_conn()
    try:
        conn.execute("""CREATE TABLE IF NOT EXISTS recent_queries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT NOT NULL,
            asked_at INTEGER DEFAULT (strftime('%s','now'))
        )""")
        conn.commit()
        rows = conn.execute(
            "SELECT question FROM recent_queries ORDER BY asked_at DESC LIMIT 3"
        ).fetchall()
        return jsonify({"recent": [r[0] for r in rows]})
    except Exception as e:
        return jsonify({"recent": []})
    finally:
        conn.close()'''

new = '''@app.route("/recent")
def recent():
    from database import get_conn
    conn = get_conn()
    try:
        conn.execute("""CREATE TABLE IF NOT EXISTS recent_queries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT NOT NULL,
            asked_at INTEGER DEFAULT (strftime('%s','now'))
        )""")
        conn.commit()
        rows = conn.execute(
            "SELECT question FROM recent_queries ORDER BY asked_at DESC LIMIT 30"
        ).fetchall()
        # Filter out short/vague follow-ups (less than 15 chars)
        filtered = [r[0] for r in rows if len(r[0].strip()) >= 15][:3]
        return jsonify({"recent": filtered})
    except Exception as e:
        return jsonify({"recent": []})
    finally:
        conn.close()


@app.route("/recent-debug")
def recent_debug():
    import hashlib
    from database import get_conn
    conn = get_conn()
    try:
        rows = conn.execute(
            "SELECT question, asked_at FROM recent_queries ORDER BY asked_at DESC LIMIT 50"
        ).fetchall()
        items = []
        for r in rows:
            q = r[0]
            qhash = hashlib.sha256(q.strip().lower().encode()).hexdigest()[:16]
            cached = conn.execute(
                "SELECT answer, hit_count FROM response_cache WHERE question_hash=?", (qhash,)
            ).fetchone()
            items.append({
                "question": q,
                "answer": cached[0][:600] if cached else None,
                "hit_count": cached[1] if cached else 0,
                "asked_at": r[1]
            })
        html = """<html><head><style>
            body{font-family:sans-serif;max-width:900px;margin:40px auto;background:#111;color:#eee;padding:20px}
            h2{color:#7d0a1c;margin-bottom:20px}
            .item{border:1px solid #333;border-radius:6px;padding:16px;margin-bottom:12px}
            .q{font-weight:bold;color:#d4a94f;margin-bottom:6px;cursor:pointer}
            .a{color:#aaa;font-size:.88em;white-space:pre-wrap;margin-top:8px;border-top:1px solid #222;padding-top:8px}
            .meta{font-size:.72em;color:#555;margin-bottom:4px}
            .no-cache{color:#444;font-size:.85em}
        </style></head><body>"""
        html += f"<h2>Recent Queries ({len(items)} total)</h2>"
        for item in items:
            html += f"<div class='item'>"
            html += f"<div class='meta'>{item['asked_at']} &nbsp;|&nbsp; cache hits: {item['hit_count']}</div>"
            html += f"<div class='q'>Q: {item['question']}</div>"
            if item['answer']:
                preview = item['answer'] + ('...' if len(item['answer']) >= 600 else '')
                html += f"<div class='a'>{preview}</div>"
            else:
                html += "<div class='no-cache'>No cached answer</div>"
            html += "</div>"
        html += "</body></html>"
        return html
    except Exception as e:
        return f"Error: {e}"
    finally:
        conn.close()'''

content = content.replace(old, new)
open('app.py', 'w', encoding='utf-8').write(content)
print("done")
