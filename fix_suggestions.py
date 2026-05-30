content = open('templates/index.html', encoding='utf-8').read()

# Replace the suggestions grid HTML
old_suggestions = """    <div id="suggestions">
      <button class="suggestion" onclick="ask('Who has the most championships?')"><span class="cat">Rings</span><span class="label">Who has the most championships?</span><span class="arr">›</span></button>
      <button class="suggestion" onclick="ask('What is the highest single-game score ever?')"><span class="cat">Record</span><span class="label">Highest single-game score ever?</span><span class="arr">›</span></button>
      <button class="suggestion" onclick="ask('What was the worst trade in league history?')"><span class="cat">Trade</span><span class="label">Worst trade in league history?</span><span class="arr">›</span></button>
      <button class="suggestion" onclick="ask('Who drafts the best?')"><span class="cat">Draft</span><span class="label">Who drafts the best?</span><span class="arr">›</span></button>
      <button class="suggestion" onclick="ask('Most points scored in a season?')"><span class="cat">Season</span><span class="label">Most points scored in a season?</span><span class="arr">›</span></button>
      <button class="suggestion" onclick="ask('Which manager has the best all-time record?')"><span class="cat">Record</span><span class="label">Best all-time record?</span><span class="arr">›</span></button>
    </div>"""

new_suggestions = """    <div id="suggestions">
      <button class="suggestion" onclick="ask('Who has the most championships?')"><span class="cat">Rings</span><span class="label">Who has the most championships?</span><span class="arr">›</span></button>
      <button class="suggestion recent-slot" id="recent-0" style="display:none"><span class="cat recent-cat"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width:11px;height:11px;margin-right:3px;vertical-align:middle"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>Recent</span><span class="label recent-label"></span></button>
      <button class="suggestion" onclick="ask('What is the highest single-game score ever?')"><span class="cat">Record</span><span class="label">Highest single-game score ever?</span><span class="arr">›</span></button>
      <button class="suggestion recent-slot" id="recent-1" style="display:none"><span class="cat recent-cat"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width:11px;height:11px;margin-right:3px;vertical-align:middle"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>Recent</span><span class="label recent-label"></span></button>
      <button class="suggestion" onclick="ask('Who has the best all-time record?')"><span class="cat">Record</span><span class="label">Best all-time records?</span><span class="arr">›</span></button>
      <button class="suggestion recent-slot" id="recent-2" style="display:none"><span class="cat recent-cat"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width:11px;height:11px;margin-right:3px;vertical-align:middle"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>Recent</span><span class="label recent-label"></span></button>
    </div>"""

content = content.replace(old_suggestions, new_suggestions)

# Add CSS for recent cat
recent_css = """
    .recent-cat{ color:var(--muted) !important;display:flex;align-items:center; }
"""
content = content.replace('  </style>', recent_css + '  </style>')

# Add JS to load recent queries after DOM ready
recent_js = """
async function loadRecentQueries() {
  try {
    const resp = await fetch('/recent');
    const data = await resp.json();
    const recents = data.recent || [];
    recents.forEach((q, i) => {
      const btn = document.getElementById('recent-' + i);
      if (btn && q) {
        btn.querySelector('.recent-label').textContent = q;
        btn.onclick = () => ask(q);
        btn.style.display = 'flex';
      }
    });
  } catch(e) {}
}
document.addEventListener('DOMContentLoaded', loadRecentQueries);
"""
content = content.replace('</script>', recent_js + '\n</script>')

open('templates/index.html', 'w', encoding='utf-8').write(content)
print("done")
