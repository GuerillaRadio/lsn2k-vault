content = open('app.py', encoding='utf-8').read()

old = """        rows_html = "".join(f\"\"\"<tr>
            <td>{r['model']}</td><td>{r['calls']:,}</td>
            <td>{(r['tin'] or 0):,}</td><td>{(r['tout'] or 0):,}</td>
            <td>${(r['total_cost'] or 0):.4f}</td>
        </tr>\"\"\" for r in rows)"""

new = """        def iv(x): return int(x) if x is not None else 0
        def fv(x): return float(x) if x is not None else 0.0
        rows_html = "".join(f\"\"\"<tr>
            <td>{r['model']}</td><td>{iv(r['calls']):,}</td>
            <td>{iv(r['tin']):,}</td><td>{iv(r['tout']):,}</td>
            <td>${fv(r['total_cost']):.4f}</td>
        </tr>\"\"\" for r in rows)"""

content = content.replace(old, new)

old2 = '        daily_html = "".join(f"<tr><td>{r[\'day\']}</td><td>${(r[\'daily\'] or 0):.4f}</td></tr>" for r in recent)'
new2 = '        daily_html = "".join(f"<tr><td>{r[\'day\']}</td><td>${float(r[\'daily\'] or 0):.4f}</td></tr>" for r in recent)'

content = content.replace(old2, new2)
open('app.py', 'w', encoding='utf-8').write(content)
print("done")
