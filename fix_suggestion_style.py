content = open('templates/index.html', encoding='utf-8').read()

# 1. Replace text cat labels with emoji on fixed prompts
replacements = {
    '<span class="cat">Rings</span>': '<span class="cat">💍</span>',
    '<span class="cat">Record</span>': '<span class="cat">📊</span>',
    '<span class="cat">Heartbreak</span>': '<span class="cat">💔</span>',
    '<span class="cat">Trade</span>': '<span class="cat">🔄</span>',
    '<span class="cat">Draft</span>': '<span class="cat">📋</span>',
    '<span class="cat">Season</span>': '<span class="cat">📅</span>',
}
for old, new in replacements.items():
    content = content.replace(old, new)

# 2. Fix recent buttons: stopwatch on LEFT, chevron on RIGHT, brighter
for i in range(3):
    old = f'<button class="suggestion suggestion-recent" id="recent-{i}"><span class="cat recent-cat">Recent</span><span class="label recent-label">Loading...</span><span class="recent-icon">⏱</span></button>'
    new = f'<button class="suggestion suggestion-recent" id="recent-{i}"><span class="recent-icon-left">⏱</span><span class="label recent-label">Loading...</span><span class="arr">›</span></button>'
    content = content.replace(old, new)

# 3. Update CSS: brighter suggestions, recent icon left style
import re

# Brighten suggestion colors
content = content.replace(
    'color:#d0d0d0;padding:12px 14px;',
    'color:#e0e0e0;padding:12px 14px;'
)
content = content.replace(
    '.suggestion:hover{background:#1c1010;border-left-color:var(--crimson-hi);color:#fff;}',
    '.suggestion:hover{background:#221010;border-left-color:var(--crimson-hi);color:#fff;}'
)

# Add recent-icon-left CSS
new_css = """
    .recent-icon-left{
      color:#aaa;font-size:.85rem;flex-shrink:0;margin-right:10px;
    }
    .recent-icon{ display:none; }
"""
content = content.replace('  </style>', new_css + '  </style>')

# Update cat span for emoji - smaller padding, centered
import re
old_cat = """.suggestion .cat{
      font-family:"Oswald",sans-serif;font-size:.63rem;font-weight:600;
      letter-spacing:1.5px;color:var(--pink);text-transform:uppercase;
      flex-shrink:0;width:54px;
    }"""
new_cat = """.suggestion .cat{
      font-size:.95rem;flex-shrink:0;width:28px;text-align:center;
      display:flex;align-items:center;justify-content:center;
    }"""
content = content.replace(old_cat, new_cat)

open('templates/index.html', 'w', encoding='utf-8').write(content)
print("done")
