content = open('templates/index.html', encoding='utf-8').read()

old = """const RECENT_DEFAULTS = ["Worst trade in league history?", "Who has the most playoff appearances without a ring?", "Who drafts the best?"];

async function loadRecentQueries() {
  // Set defaults first
  RECENT_DEFAULTS.forEach((q, i) => {
    const btn = document.getElementById('recent-' + i);
    if (btn) {
      btn.querySelector('.recent-label').textContent = q;
      btn.onclick = () => ask(q);
    }
  });"""

new = """const RECENT_DEFAULTS = [
  "Worst trade in league history?",
  "Who drafts the best?",
  "Which manager has never missed the playoffs?"
];

async function loadRecentQueries() {
  // Set defaults first
  RECENT_DEFAULTS.forEach((q, i) => {
    const btn = document.getElementById('recent-' + i);
    if (btn) {
      btn.querySelector('.recent-label').textContent = q;
      btn.onclick = () => ask(q);
    }
  });"""

content = content.replace(old, new)
open('templates/index.html', 'w', encoding='utf-8').write(content)
print("done")
