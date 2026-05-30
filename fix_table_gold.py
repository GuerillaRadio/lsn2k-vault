import re
content = open('templates/index.html', encoding='utf-8').read()

# Remove ALL gold/pink from anything table-related
# td last child gold
content = re.sub(r'\.bubble tbody td:last-child\{[^}]+\}', '', content)
content = re.sub(r'\.bubble tbody tr:first-child td:last-child\{[^}]+\}', '', content)
content = re.sub(r'\.bubble tbody tr:first-child td\{[^}]+\}', '', content)

# Make sure strong inside tables doesn't get gold either
# Add a rule that overrides strong color inside tables
table_strong = """
    .bubble table strong{ color:var(--text);font-weight:700; }
"""
content = content.replace('  </style>', table_strong + '  </style>')

open('templates/index.html', 'w', encoding='utf-8').write(content)
print("done")
