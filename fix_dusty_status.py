content = open('templates/index.html', encoding='utf-8').read()
content = content.replace(
    '"Writing Dusty Butler a green slip for calling me a dickhead..."',
    '"Writing Dusty Butler a green slip for calling me a cocksucker in the hallway..."'
)
open('templates/index.html', 'w', encoding='utf-8').write(content)
print("done")
