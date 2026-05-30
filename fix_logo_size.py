import re
content = open('templates/index.html', encoding='utf-8').read()

content = re.sub(
    r'\.logo-hero\{[^}]+\}',
    '''.logo-hero{
      width:auto;max-width:min(400px,55vw);max-height:32vh;
      object-fit:contain;
      filter:drop-shadow(0 6px 28px rgba(110,7,23,.45));
      margin-bottom:20px;
    }''',
    content
)

open('templates/index.html', 'w', encoding='utf-8').write(content)
print("done")
