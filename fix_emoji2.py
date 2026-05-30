import re
content = open('templates/index.html', encoding='utf-8').read()

# Fix .suggestion .cat - remove fixed width, match recent icon sizing
content = re.sub(
    r'\.suggestion \.cat\{[^}]+\}',
    '''.suggestion .cat{
      font-size:1.1rem;flex-shrink:0;line-height:1;
      display:flex;align-items:center;justify-content:center;
    }''',
    content
)

# Also fix the mobile override for .cat
content = content.replace(
    '.suggestion .cat{ width:46px;font-size:.58rem; }',
    '.suggestion .cat{ font-size:.9rem; }'
)

open('templates/index.html', 'w', encoding='utf-8').write(content)
print("done")
