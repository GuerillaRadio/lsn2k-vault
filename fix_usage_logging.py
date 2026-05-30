content = open('src/chat.py', encoding='utf-8').read()

old = """            # Log token usage
            try:
                u = final.usage
                inp = getattr(u, 'input_tokens', 0) or 0
                out = getattr(u, 'output_tokens', 0) or 0
                cache = getattr(u, 'cache_read_input_tokens', 0) or 0
                # Sonnet pricing
                cost = (inp * 3.0 + out * 15.0 + cache * 0.3) / 1_000_000
                from database import get_conn as _gc
                _c = _gc()
                _c.execute("CREATE TABLE IF NOT EXISTS usage_log (id INTEGER PRIMARY KEY AUTOINCREMENT, model TEXT, input_tokens INTEGER, output_tokens INTEGER, cache_read_tokens INTEGER, cost_usd REAL, asked_at INTEGER DEFAULT (strftime('%s','now')))")
                _c.execute("INSERT INTO usage_log (model,input_tokens,output_tokens,cache_read_tokens,cost_usd) VALUES (?,?,?,?,?)",
                           (MODEL, inp, out, cache, round(cost, 6)))
                _c.commit()
                _c.close()
            except Exception:
                pass"""

new = """            # Log token usage
            try:
                u = final.usage
                inp = getattr(u, 'input_tokens', 0) or 0
                out = getattr(u, 'output_tokens', 0) or 0
                cache = getattr(u, 'cache_read_input_tokens', 0) or 0
                cost = round((inp * 3.0 + out * 15.0 + cache * 0.3) / 1_000_000, 6)
                import requests as _req, os as _os
                _url = _os.getenv("TURSO_URL", "").replace("libsql://","https://")
                _tok = _os.getenv("TURSO_TOKEN","")
                if _url and _tok:
                    _sql = f"INSERT INTO usage_log (model,input_tokens,output_tokens,cache_read_tokens,cost_usd) VALUES ('{MODEL}',{inp},{out},{cache},{cost})"
                    _req.post(f"{_url}/v2/pipeline",
                        headers={"Authorization":f"Bearer {_tok}","Content-Type":"application/json"},
                        json={"requests":[{"type":"execute","stmt":{"sql":_sql}},{"type":"close"}]},
                        timeout=5)
            except Exception:
                pass"""

content = content.replace(old, new)
open('src/chat.py', 'w', encoding='utf-8').write(content)
print("done")
