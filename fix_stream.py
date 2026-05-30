content = open('templates/index.html', encoding='utf-8').read()
content = content.replace(
    'bubble.innerHTML = formatText(fullText);',
    'bubble.textContent = fullText;'
)
open('templates/index.html', 'w', encoding='utf-8').write(content)
print("done")
