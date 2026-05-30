content = open('templates/index.html', encoding='utf-8').read()

old = """.bubble thead th{

      background:#2a1a1d;color:#c9a0a8;font-family:"Roboto",sans-serif;

      font-weight:700;font-variant:small-caps;letter-spacing:.08em;

      font-size:.8rem;padding:9px 13px;text-align:left;border-bottom:1px solid #4a2a30;

    }"""

new = """.bubble thead th{
      background:#5a0616;color:#f0d0d5;font-family:"Roboto",sans-serif;
      font-weight:700;text-transform:uppercase;letter-spacing:.08em;
      font-size:.74rem;padding:9px 13px;text-align:left;
    }"""

if old in content:
    content = content.replace(old, new)
    print("replaced thead th")
else:
    # Try normalizing whitespace
    import re
    content = re.sub(
        r'\.bubble thead th\{[^}]+\}',
        new,
        content
    )
    print("replaced via regex")

# Also fix strong highlight color to something more visible
content = content.replace(
    'color:var(--pink-soft);font-weight:700;',
    'color:#f5c842;font-weight:700;'
)
print("updated highlight color to gold-yellow")

open('templates/index.html', 'w', encoding='utf-8').write(content)
print("done")
