import re
content = open('templates/index.html', encoding='utf-8').read()

# 1. Restore original gold, remove yellow highlight on bold
content = content.replace('color:#f5c842;font-weight:700;', 'color:var(--text);font-weight:700;')

# 2. Table header font color → white
content = re.sub(
    r'(\.bubble thead th\{[^}]+)color:#f0d0d5;',
    r'\1color:#fff;',
    content
)

# 3. More table margin
content = content.replace(
    '.bubble table{',
    '.bubble table{ margin:1.4em 0 !important;'
)
# Remove duplicate margin from existing rule
content = re.sub(
    r'(\.bubble table\{[^}]+?)margin:\.8em 0;',
    r'\1',
    content
)

# 4. More line/paragraph spacing
content = content.replace(
    'padding:13px 17px;line-height:1.62;font-size:.93rem;border-radius:12px;',
    'padding:16px 20px;line-height:1.85;font-size:.93rem;border-radius:12px;'
)
content = content.replace(
    '.bubble p{margin-bottom:.6em;}',
    '.bubble p{margin-bottom:.9em;}'
)

# 5. Remove "League AI" from nameplate - update in the JS addMessage function
content = content.replace(
    "np.innerHTML = 'Coach Taylor <b>League AI</b>';",
    "np.innerHTML = 'Coach Taylor';"
)
# Also fix the streaming bubble
content = content.replace(
    'np.innerHTML = \'Coach Taylor <b>League AI</b>\';',
    'np.innerHTML = \'Coach Taylor\';'
)

open('templates/index.html', 'w', encoding='utf-8').write(content)
print("done")
