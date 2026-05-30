import re
content = open('templates/index.html', encoding='utf-8').read()

DEFAULTS = [
    "Worst trade in league history?",
    "Who has the most playoff appearances without a ring?",
    "Who drafts the best?",
]

# Fix: show recent slots immediately with defaults, no display:none
for i, default in enumerate(DEFAULTS):
    content = content.replace(
        f'id="recent-{i}" style="display:none"',
        f'id="recent-{i}"'
    )
    content = content.replace(
        f'id="recent-{i}"><span class="cat recent-cat">',
        f'id="recent-{i}" data-default="{default}" onclick="ask(\'{default}\')"><span class="cat recent-cat">'
    )

# Fix: use a simple clock emoji instead of SVG inside the cat label
# Remove the SVG inside cat spans and use text instead
content = re.sub(
    r'<svg[^>]*viewBox="0 0 24 24"[^>]*>.*?</svg>Recent',
    '⏱ Recent',
    content,
    flags=re.DOTALL
)

# Fix the recent-label defaults
old_js = """async function loadRecentQueries() {
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
document.addEventListener('DOMContentLoaded', loadRecentQueries);"""

new_js = """const RECENT_DEFAULTS = """ + str(DEFAULTS).replace("'", '"') + """;

async function loadRecentQueries() {
  // Set defaults first
  RECENT_DEFAULTS.forEach((q, i) => {
    const btn = document.getElementById('recent-' + i);
    if (btn) {
      btn.querySelector('.recent-label').textContent = q;
      btn.onclick = () => ask(q);
    }
  });
  // Then try to load actual recents
  try {
    const resp = await fetch('/recent');
    const data = await resp.json();
    const recents = data.recent || [];
    recents.forEach((q, i) => {
      const btn = document.getElementById('recent-' + i);
      if (btn && q) {
        btn.querySelector('.recent-label').textContent = q;
        btn.onclick = () => ask(q);
      }
    });
  } catch(e) {}
}
document.addEventListener('DOMContentLoaded', loadRecentQueries);"""

content = content.replace(old_js, new_js)

open('templates/index.html', 'w', encoding='utf-8').write(content)
print("done")
