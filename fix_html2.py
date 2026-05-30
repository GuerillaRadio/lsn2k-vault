content = open('templates/index.html', 'rb').read().decode('utf-8', errors='replace')
content = content.replace(chr(0), '')

# Fix: single newlines within a paragraph should become a space (not br, not nothing)
old = "p.replace(/\\n/g,' ')"
new = "p.replace(/\\n/g,' ')"
# Check if already applied
if old in content:
    print("newline fix already applied")
else:
    # Find the old br version
    content = content.replace("p.replace(/\\n/g,'<br>')", "p.replace(/\\n/g,' ')")
    print("applied br->space fix")

# Also fix: period immediately followed by capital letter with no space
# This handles cases where Claude joins lines without space e.g. "records.Eric"
old2 = ".join('');"
new2 = """.replace(/\\.([A-Z])/g, '. $1').join('');"""
if "replace(/\\\\." not in content:
    content = content.replace(".join('');", ".replace(/\\.([A-Z])/g, '. $1').join('');")
    print("applied period-space fix")

open('templates/index.html', 'w', encoding='utf-8').write(content)
print("done")
