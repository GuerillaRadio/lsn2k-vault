"""Flask web app — fantasy football AI chat interface."""

import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from flask import Flask, render_template, request, jsonify, session, Response, stream_with_context
from chat import chat_stream

app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = os.getenv("FLASK_SECRET_KEY", "lsn2000-chieeeeeeefs-secret-dev")


@app.route("/")
def index():
    session.setdefault("messages", [])
    from database import get_conn
    conn = get_conn()
    season_count = conn.execute("SELECT COUNT(*) FROM leagues").fetchone()[0]
    conn.close()
    return render_template("index.html", season_count=season_count)


@app.route("/chat", methods=["POST"])
def handle_chat():
    data = request.get_json()
    user_text = data.get("message", "").strip()
    if not user_text:
        return jsonify({"error": "Empty message"}), 400

    messages = session.get("messages", [])
    messages.append({"role": "user", "content": user_text})
    session["messages"] = messages
    session.modified = True

    # Log to recent queries
    try:
        from database import get_conn
        conn = get_conn()
        conn.execute("CREATE TABLE IF NOT EXISTS recent_queries (id INTEGER PRIMARY KEY AUTOINCREMENT, question TEXT NOT NULL, asked_at INTEGER DEFAULT (strftime('%s','now')))")
        conn.execute("INSERT INTO recent_queries (question) VALUES (?)", (user_text,))
        conn.commit()
        conn.close()
    except Exception:
        pass

    def generate():
        try:
            for chunk in chat_stream(list(messages), original_question=user_text):
                yield chunk
        except Exception as e:
            import json
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return Response(
        stream_with_context(generate()),
        content_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        }
    )


@app.route("/recent")
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
        conn.close()


@app.route("/save", methods=["POST"])
def save_message():
    """Save the completed assistant message to session history."""
    data = request.get_json()
    content = data.get("content", [])
    messages = session.get("messages", [])
    messages.append({"role": "assistant", "content": content})
    session["messages"] = messages
    session.modified = True
    return jsonify({"ok": True})


@app.route("/rate", methods=["POST"])
def rate():
    data = request.get_json()
    from database import get_conn
    import time
    conn = get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS response_ratings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rating INTEGER,
            response_preview TEXT,
            created_at INTEGER DEFAULT (strftime('%s','now'))
        )
    """)
    conn.execute("INSERT INTO response_ratings (rating, response_preview) VALUES (?,?)",
                 (data.get("rating"), data.get("text", "")[:300]))
    conn.commit()
    conn.close()
    return jsonify({"ok": True})


@app.route("/health")
def health():
    import os
    turso_url = os.getenv("TURSO_URL", "NOT SET")
    turso_token = os.getenv("TURSO_TOKEN", "NOT SET")
    try:
        from database import get_conn
        conn = get_conn()
        count = conn.execute("SELECT COUNT(*) FROM leagues").fetchone()[0]
        return jsonify({"status": "ok", "leagues": count, "turso_url": turso_url[:30], "token_set": turso_token != "NOT SET"})
    except Exception as e:
        return jsonify({"status": "error", "error": str(e), "turso_url": turso_url[:30], "token_set": turso_token != "NOT SET"})


@app.route("/reset", methods=["POST"])
def reset():
    session["messages"] = []
    session.modified = True
    return jsonify({"ok": True})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
