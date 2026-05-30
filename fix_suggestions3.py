import re
content = open('templates/index.html', encoding='utf-8').read()

# Replace the entire suggestions div with the correct 3+3 layout
old = re.search(r'<div id="suggestions">.*?</div>', content, re.DOTALL).group(0)

new = """<div id="suggestions">
      <button class="suggestion" onclick="ask('Who has the most championships?')"><span class="cat">Rings</span><span class="label">Who has the most championships?</span><span class="arr">›</span></button>
      <button class="suggestion" id="recent-0" onclick="ask('Worst trade in league history?')"><span class="cat recent-cat">⏱ Recent</span><span class="label recent-label">Worst trade in league history?</span></button>
      <button class="suggestion" onclick="ask('What is the highest single-game score ever?')"><span class="cat">Record</span><span class="label">Highest single-game score ever?</span><span class="arr">›</span></button>
      <button class="suggestion" id="recent-1" onclick="ask('Who has the most playoff appearances without a ring?')"><span class="cat recent-cat">⏱ Recent</span><span class="label recent-label">Who has the most playoff appearances without a ring?</span></button>
      <button class="suggestion" onclick="ask('Who has the best all-time record?')"><span class="cat">Record</span><span class="label">Best all-time records?</span><span class="arr">›</span></button>
      <button class="suggestion" id="recent-2" onclick="ask('Who drafts the best?')"><span class="cat recent-cat">⏱ Recent</span><span class="label recent-label">Who drafts the best?</span></button>
    </div>"""

content = content.replace(old, new)
open('templates/index.html', 'w', encoding='utf-8').write(content)
print("done")
