import re
content = open('templates/index.html', encoding='utf-8').read()

# Fix recent buttons to have the gray "Recent" label on the left and ⏱ on the right
for i in range(3):
    old = f'<button class="suggestion suggestion-recent" id="recent-{i}"><span class="label recent-label">Loading...</span><span class="recent-icon">⏱</span></button>'
    new = f'<button class="suggestion suggestion-recent" id="recent-{i}"><span class="cat recent-cat">Recent</span><span class="label recent-label">Loading...</span><span class="recent-icon">⏱</span></button>'
    content = content.replace(old, new)

open('templates/index.html', 'w', encoding='utf-8').write(content)
print("done")
