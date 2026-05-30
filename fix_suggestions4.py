import re
content = open('templates/index.html', encoding='utf-8').read()

# 1. Replace suggestions grid with new layout
old = re.search(r'<div id="suggestions">.*?</div>', content, re.DOTALL).group(0)

new = """<div id="suggestions">
      <!-- 2x2 fixed prompts -->
      <div class="suggestions-fixed">
        <button class="suggestion" onclick="ask('Who has the most championships?')"><span class="cat">Rings</span><span class="label">Who has the most championships?</span><span class="arr">›</span></button>
        <button class="suggestion" onclick="ask('What is the highest single-game score ever?')"><span class="cat">Record</span><span class="label">Highest single-game score ever?</span><span class="arr">›</span></button>
        <button class="suggestion" onclick="ask('Who has the best all-time record?')"><span class="cat">Record</span><span class="label">Best all-time records?</span><span class="arr">›</span></button>
        <button class="suggestion" onclick="ask('Who has the most playoff appearances without a championship?')"><span class="cat">Heartbreak</span><span class="label">Most playoffs, no ring?</span><span class="arr">›</span></button>
      </div>
      <!-- 3 recent queries, full width -->
      <div class="suggestions-recent">
        <button class="suggestion suggestion-recent" id="recent-0"><span class="label recent-label">Loading...</span><span class="recent-icon">⏱</span></button>
        <button class="suggestion suggestion-recent" id="recent-1"><span class="label recent-label">Loading...</span><span class="recent-icon">⏱</span></button>
        <button class="suggestion suggestion-recent" id="recent-2"><span class="label recent-label">Loading...</span><span class="recent-icon">⏱</span></button>
      </div>
    </div>"""

content = content.replace(old, new)

# 2. Update CSS for the new layout
old_css = """    #suggestions{
      display:grid;grid-template-columns:1fr 1fr;gap:9px;
      max-width:820px;width:100%;margin-top:26px;
    }"""

new_css = """    #suggestions{
      display:flex;flex-direction:column;gap:9px;
      max-width:820px;width:100%;margin-top:26px;
    }
    .suggestions-fixed{
      display:grid;grid-template-columns:1fr 1fr;gap:9px;
    }
    .suggestions-recent{
      display:flex;flex-direction:column;gap:7px;
      margin-top:2px;
    }
    .suggestion-recent{
      width:100%;justify-content:space-between;
    }
    .suggestion-recent .recent-label{ flex:1;text-align:left; }
    .recent-icon{ color:var(--dim);font-size:.9rem;flex-shrink:0;margin-left:10px; }"""

content = content.replace(old_css, new_css)

# 3. Mobile: show only 2 recents
content = content.replace(
    '#suggestions .suggestion:nth-child(n+3){ display:none; }',
    '.suggestions-recent .suggestion-recent:nth-child(n+3){ display:none; }'
)

open('templates/index.html', 'w', encoding='utf-8').write(content)
print("done")
