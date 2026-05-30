content = open('templates/index.html', encoding='utf-8').read()

# Replace DOMContentLoaded with immediate call + also call when landing is shown
old = 'document.addEventListener(\'DOMContentLoaded\', loadRecentQueries);'
new = '// Call immediately and also ensure it runs after any dynamic rendering\nloadRecentQueries();\nwindow.addEventListener(\'load\', loadRecentQueries);'

content = content.replace(old, new)

open('templates/index.html', 'w', encoding='utf-8').write(content)
print("done")
