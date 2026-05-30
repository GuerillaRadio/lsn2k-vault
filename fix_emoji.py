content = open('templates/index.html', encoding='utf-8').read()

# Bigger emoji in cat span
content = content.replace(
    'font-size:.95rem;flex-shrink:0;width:28px;text-align:center;\n      display:flex;align-items:center;justify-content:center;',
    'font-size:1.2rem;flex-shrink:0;width:32px;text-align:center;\n      display:flex;align-items:center;justify-content:center;line-height:1;'
)

# Replace ⏱ text with stopwatch emoji (already is ⏱ but let's use the cleaner ⏱️)
content = content.replace('>⏱</span>', '>⏱️</span>')

# Slightly bigger stopwatch icon
content = content.replace(
    'color:#aaa;font-size:.85rem;flex-shrink:0;margin-right:10px;',
    'color:#bbb;font-size:1.1rem;flex-shrink:0;margin-right:10px;line-height:1;'
)

open('templates/index.html', 'w', encoding='utf-8').write(content)
print("done")
