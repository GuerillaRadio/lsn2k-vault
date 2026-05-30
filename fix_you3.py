import re
content = open('templates/index.html', encoding='utf-8').read()

content = re.sub(
    r'(\.user-avatar\{[^}]+)font-weight:700;',
    r'\1font-weight:400;',
    content
)

open('templates/index.html', 'w', encoding='utf-8').write(content)
print("done")
