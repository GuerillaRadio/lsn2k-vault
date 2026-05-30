import re
content = open('templates/index.html', encoding='utf-8').read()

content = re.sub(
    r'(#reset-btn\{[^}]+)font-family:"Roboto",sans-serif;',
    r'\1font-family:"Oswald",sans-serif;',
    content
)

open('templates/index.html', 'w', encoding='utf-8').write(content)
print("done")
