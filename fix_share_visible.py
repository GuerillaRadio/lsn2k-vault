content = open('templates/index.html', encoding='utf-8').read()
# Make share button always visible temporarily to debug
content = content.replace(
    '.msg-actions{\n      display:flex;justify-content:flex-end;margin-top:6px;opacity:0;\n      transition:opacity .15s;\n    }',
    '.msg-actions{\n      display:flex;justify-content:flex-end;margin-top:6px;opacity:1;\n      transition:opacity .15s;\n    }'
)
open('templates/index.html', 'w', encoding='utf-8').write(content)
print("share button now always visible")
