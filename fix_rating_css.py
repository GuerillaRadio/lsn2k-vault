content = open('templates/index.html', encoding='utf-8').read()

extra_css = """
    .thumb-btn{ padding:4px 8px; }
    .thumb-btn.rated{ border-color:var(--gold);color:var(--gold); }
    .nameplate.user-nameplate{color:var(--muted);}
"""
content = content.replace('  </style>', extra_css + '  </style>')
open('templates/index.html', 'w', encoding='utf-8').write(content)
print("done")
