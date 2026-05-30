content = open('app.py', encoding='utf-8').read()

new_endpoints = '''
@app.route("/quality")
def quality():
    from database import get_conn
    conn = get_conn()
    try:
        rows = conn.execute("""
            SELECT r.id, r.rating, r.response_preview, r.created_at,
                   rq.question
            FROM response_ratings r
            LEFT JOIN recent_queries rq ON ABS(r.created_at - rq.asked_at) < 5
            ORDER BY r.created_at DESC LIMIT 100
        """).fetchall()
        thumbs_down = [r for r in rows if r["rating"] == -1]
        thumbs_up   = [r for r in rows if r["rating"] == 1]

        def card(r, color):
            q = r["question"] or ""
            preview = r["response_preview"] or ""
            return f"""<div style="background:#1a1a1a;border:1px solid {'#c0392b' if color=='red' else '#27ae60'};border-radius:6px;padding:14px;margin-bottom:10px">
                <div style="font-size:.75rem;color:#555;margin-bottom:4px">{r['created_at']}</div>
                {"<div style='color:#d4a94f;font-size:.85rem;margin-bottom:6px'>Q: " + q[:120] + "</div>" if q else ""}
                <div style="color:#aaa;font-size:.82rem;white-space:pre-wrap">{preview[:400]}</div>
            </div>"""

        html = f"""<!DOCTYPE html><html><head><title>Quality Review</title>
        <style>body{{font-family:sans-serif;background:#0a0a0a;color:#eee;max-width:900px;margin:40px auto;padding:20px}}
        h1{{color:#7d0a1c}} h2{{color:#d4a94f;margin:24px 0 12px}} .stats{{display:flex;gap:20px;margin-bottom:24px}}
        .stat{{background:#1a1a1a;border:1px solid #333;border-radius:8px;padding:16px 24px;text-align:center}}
        .stat .n{{font-size:2rem;font-weight:700}} .stat .l{{font-size:.8rem;color:#888}}</style></head><body>
        <h1>Quality Review</h1>
        <div class="stats">
            <div class="stat"><div class="n" style="color:#27ae60">{len(thumbs_up)}</div><div class="l">👍 Thumbs Up</div></div>
            <div class="stat"><div class="n" style="color:#c0392b">{len(thumbs_down)}</div><div class="l">👎 Thumbs Down</div></div>
            <div class="stat"><div class="n">{len(rows)}</div><div class="l">Total Ratings</div></div>
        </div>
        <h2>👎 Thumbs Down ({len(thumbs_down)})</h2>
        {"".join(card(r,"red") for r in thumbs_down) or "<p style='color:#555'>None yet.</p>"}
        <h2>👍 Thumbs Up ({len(thumbs_up)})</h2>
        {"".join(card(r,"green") for r in thumbs_up[:20]) or "<p style='color:#555'>None yet.</p>"}
        </body></html>"""
        return html
    except Exception as e:
        return f"Error: {e}"
    finally:
        conn.close()


@app.route("/costs")
def costs():
    from database import get_conn
    conn = get_conn()
    try:
        # Sonnet pricing: $3/$15 per million input/output tokens
        INPUT_COST  = 3.00 / 1_000_000
        OUTPUT_COST = 15.00 / 1_000_000
        CACHE_COST  = 0.30 / 1_000_000  # cache reads

        rows = conn.execute("""
            SELECT model, SUM(input_tokens) as tin, SUM(output_tokens) as tout,
                   SUM(cache_read_tokens) as tcache, COUNT(*) as calls,
                   SUM(cost_usd) as total_cost
            FROM usage_log GROUP BY model ORDER BY total_cost DESC
        """).fetchall()

        total = sum(r["total_cost"] or 0 for r in rows)
        recent = conn.execute("""
            SELECT DATE(asked_at,'unixepoch') as day, SUM(cost_usd) as daily
            FROM usage_log GROUP BY day ORDER BY day DESC LIMIT 14
        """).fetchall()

        rows_html = "".join(f"""<tr>
            <td>{r['model']}</td><td>{r['calls']:,}</td>
            <td>{(r['tin'] or 0):,}</td><td>{(r['tout'] or 0):,}</td>
            <td>${(r['total_cost'] or 0):.4f}</td>
        </tr>""" for r in rows)

        daily_html = "".join(f"<tr><td>{r['day']}</td><td>${(r['daily'] or 0):.4f}</td></tr>" for r in recent)

        html = f"""<!DOCTYPE html><html><head><title>Cost Monitor</title>
        <style>body{{font-family:sans-serif;background:#0a0a0a;color:#eee;max-width:800px;margin:40px auto;padding:20px}}
        h1{{color:#7d0a1c}} h2{{color:#d4a94f;margin:24px 0 12px}}
        .total{{font-size:2.5rem;font-weight:700;color:#d4a94f;margin:20px 0}}
        table{{border-collapse:collapse;width:100%;margin-bottom:24px}}
        th,td{{border:1px solid #333;padding:8px 12px;text-align:left}}
        th{{background:#1a1a1a;color:#888;font-size:.8rem;text-transform:uppercase}}
        tr:nth-child(even) td{{background:#111}}</style></head><body>
        <h1>Cost Monitor</h1>
        <div class="total">Total: ${total:.4f}</div>
        <p style="color:#555;font-size:.85rem">Sonnet: $3/$15 per million input/output tokens</p>
        <h2>By Model</h2>
        <table><thead><tr><th>Model</th><th>Calls</th><th>Input Tokens</th><th>Output Tokens</th><th>Cost</th></tr></thead>
        <tbody>{rows_html or "<tr><td colspan=5 style='color:#555'>No data yet</td></tr>"}</tbody></table>
        <h2>Last 14 Days</h2>
        <table><thead><tr><th>Date</th><th>Cost</th></tr></thead>
        <tbody>{daily_html or "<tr><td colspan=2 style='color:#555'>No data yet</td></tr>"}</tbody></table>
        </body></html>"""
        return html
    except Exception as e:
        return f"Error: {e}"
    finally:
        conn.close()

'''

# Insert before the reset route
content = content.replace('@app.route("/reset", methods=["POST"])', new_endpoints + '@app.route("/reset", methods=["POST"])')
open('app.py', 'w', encoding='utf-8').write(content)
print("done")
