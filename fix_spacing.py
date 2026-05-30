content = open('templates/index.html', encoding='utf-8').read()
content = content.replace(
    '.suggestions-recent{\n      display:flex;flex-direction:column;gap:7px;\n    }',
    '.suggestions-recent{\n      display:flex;flex-direction:column;gap:7px;\n      margin-top:14px;\n    }'
)
open('templates/index.html', 'w', encoding='utf-8').write(content)
print("done")
