content = open('templates/index.html', encoding='utf-8').read()

content = content.replace(
    '<h2>Coach Taylor\'s here to <em>Help.</em></h2>',
    '<h2><em>Ask</em> Steve Taylor</h2>'
)

open('templates/index.html', 'w', encoding='utf-8').write(content)
print("done")
