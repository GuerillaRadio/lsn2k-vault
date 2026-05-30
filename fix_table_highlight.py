import re
content = open('templates/index.html', encoding='utf-8').read()

# Restore gold on bold text
content = content.replace(
    'color:var(--text);font-weight:700;',
    'color:var(--gold-soft);font-weight:700;'
)

# Remove the first-row special gradient highlight in tables
content = re.sub(
    r"\.bubble tbody tr:first-child td\{background:linear-gradient\([^}]+\}\s*",
    "",
    content
)
content = re.sub(
    r"\.bubble tbody tr:first-child td:last-child\{color:var\(--pink\);\}\s*",
    "",
    content
)

open('templates/index.html', 'w', encoding='utf-8').write(content)
print("done")
