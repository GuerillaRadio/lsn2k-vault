content = open('src/chat.py', encoding='utf-8').read()
content = content.replace(
    "Back in high school, Dustin Butler called Coach Taylor a dickhead to his face in front of the whole team. Coach wrote him up on the spot — green slip, sent straight to Principal Stan Elliott's office. Dusty has never lived it down.",
    "Back in high school, Dustin Butler called a friend a dickhead. Coach Taylor overheard it, wrote him up on a green slip, and marched him to Principal Elliott's office. On the way there, Dusty called Coach Taylor a cocksucker to his face in the hallway. Coach has never forgotten it."
)
open('src/chat.py', 'w', encoding='utf-8').write(content)
print("done")
