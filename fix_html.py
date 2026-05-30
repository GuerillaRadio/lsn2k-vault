content = open('templates/index.html', 'rb').read().decode('utf-8', errors='replace')
content = content.replace(chr(0), '')  # strip null bytes
# Fix single newline in paragraphs: use space instead of <br> so "sentence.\nWord" becomes "sentence. Word"
content = content.replace("p.replace(/\\n/g,'<br>')", "p.replace(/\\n/g,' ')")
open('templates/index.html', 'w', encoding='utf-8').write(content)
print('Done. Null bytes stripped and newline fix applied.')
