import re
content = open('templates/index.html', encoding='utf-8').read()

content = re.sub(
    r'\.user-avatar\{[^}]+\}',
    '''.user-avatar{
      width:38px;height:38px;border-radius:50%;flex-shrink:0;
      background:#2a2a2a;color:#bbb;display:flex;align-items:center;justify-content:center;
      font-weight:700;font-size:.72rem;font-family:"Oswald",sans-serif;
      letter-spacing:1.5px;text-transform:uppercase;
    }''',
    content
)

open('templates/index.html', 'w', encoding='utf-8').write(content)
print("done")
