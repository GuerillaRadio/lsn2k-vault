content = open('app.py', encoding='utf-8').read()
old = '        total = sum(r["total_cost"] or 0 for r in rows)'
new = '        total = sum(float(r["total_cost"] or 0) for r in rows)'
content = content.replace(old, new)
open('app.py', 'w', encoding='utf-8').write(content)
print("done")
