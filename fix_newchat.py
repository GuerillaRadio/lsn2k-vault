content = open('templates/index.html', encoding='utf-8').read()

old = """    #reset-btn{
      background:none;border:1px solid rgba(255,255,255,.4);color:rgba(255,255,255,.85);
      padding:6px 14px;border-radius:3px;cursor:pointer;font-size:.78rem;font-weight:600;
      font-family:"Public Sans",sans-serif;transition:.15s;white-space:nowrap;
    }
    #reset-btn:hover{border-color:#fff;color:#fff;background:rgba(0,0,0,.15);}"""

new = """    #reset-btn{
      background:#fff;border:none;color:var(--crimson);
      padding:6px 16px;border-radius:3px;cursor:pointer;font-size:.72rem;font-weight:700;
      font-family:"Roboto",sans-serif;text-transform:uppercase;letter-spacing:.08em;
      transition:.15s;white-space:nowrap;
    }
    #reset-btn:hover{background:rgba(255,255,255,.85);}"""

if old in content:
    content = content.replace(old, new)
    print("replaced")
else:
    import re
    content = re.sub(r'#reset-btn\{[^}]+\}\s*#reset-btn:hover\{[^}]+\}', new, content)
    print("replaced via regex")

open('templates/index.html', 'w', encoding='utf-8').write(content)
print("done")
