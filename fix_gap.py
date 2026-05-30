content = open('templates/index.html', encoding='utf-8').read()

# Remove the explicit margin-right from recent icon - let parent gap handle it
content = content.replace(
    'color:#bbb;font-size:1.1rem;flex-shrink:0;margin-right:10px;line-height:1;',
    'color:#bbb;font-size:1.1rem;flex-shrink:0;line-height:1;'
)

open('templates/index.html', 'w', encoding='utf-8').write(content)
print("done")
