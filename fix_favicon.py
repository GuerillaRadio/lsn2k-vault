content = open('templates/index.html', encoding='utf-8').read()
favicon_tags = """  <link rel="icon" type="image/x-icon" href="/static/favicon.ico"/>
  <link rel="icon" type="image/png" sizes="192x192" href="/static/favicon-192.png"/>
"""
content = content.replace('<meta charset="UTF-8"/>', '<meta charset="UTF-8"/>\n' + favicon_tags)
open('templates/index.html', 'w', encoding='utf-8').write(content)
print("done")
