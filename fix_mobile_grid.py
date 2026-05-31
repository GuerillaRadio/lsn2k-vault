content = open('templates/index.html', encoding='utf-8').read()

# Find and update the mobile suggestions-fixed override
old = '      .suggestions-recent .suggestion-recent:nth-child(n+3){ display:none; }\n      .suggestion{ padding:10px 12px;font-size:.82rem; }\n      .suggestion .cat{ font-size:.9rem; }'

new = '      .suggestions-fixed{ grid-template-columns:1fr; }\n      .suggestions-recent .suggestion-recent:nth-child(n+3){ display:none; }\n      .suggestion{ padding:10px 12px;font-size:.82rem; }\n      .suggestion .cat{ font-size:.9rem; }'

if old in content:
    content = content.replace(old, new)
    print("found and replaced")
else:
    # Try regex approach
    import re
    content = re.sub(
        r'(@media\(max-width:640px\)\{.*?)(\.suggestion\{ padding)',
        r'\1.suggestions-fixed{ grid-template-columns:1fr; }\n      \2',
        content,
        flags=re.DOTALL
    )
    print("used regex")

open('templates/index.html', 'w', encoding='utf-8').write(content)
print("done")
