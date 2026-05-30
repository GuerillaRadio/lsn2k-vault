content = open('templates/index.html', encoding='utf-8').read()

# Fix: move the regex to after .join('') where it belongs
content = content.replace(
    ".filter(Boolean).replace(/\\.",
    ".filter(Boolean).join('').replace(/\\."
)
content = content.replace(
    "'. $1').join('');",
    "'. $1');"
)

open('templates/index.html', 'w', encoding='utf-8').write(content)
print("Fixed. join is now before replace.")
