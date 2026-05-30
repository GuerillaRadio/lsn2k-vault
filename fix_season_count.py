content = open('templates/index.html', encoding='utf-8').read()

content = content.replace('23 Seasons &bull; Est. 2000', '{{ season_count }} Seasons &bull; Est. 2000')
content = content.replace('23 seasons of LSN2K history on the board', '{{ season_count }} seasons of LSN2K history on the board')
content = content.replace("'23 seasons · Est. 2000 · Steve Taylor, League Analyst'", "'{{ season_count }} seasons · Est. 2000 · Steve Taylor, League Analyst'")

open('templates/index.html', 'w', encoding='utf-8').write(content)
print("done")
