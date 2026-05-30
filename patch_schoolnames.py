content = open('src/chat.py', encoding='utf-8').read()

old = """  * "One more word and you're in Coach Henderson's office"
  * "You're two seconds from sitting the bench"
  * "That's a green slip right there"
  * "I'll call your parents"
  * "Drop and give me 20 for that take"
  * "You're on the injury report after an answer like that"
  * "That gets you laps — I don't care if it's raining"
  * "Try saying that during film review, see what happens" """

new = """  * "One more word and you're in Principal Elliott's office"
  * "Keep it up and I'm sending you to see Stan Elliott — see how that goes"
  * "You're two seconds from sitting the bench"
  * "That's a green slip right there"
  * "I'll call your parents"
  * "Drop and give me 20 for that take"
  * "You're on the injury report after an answer like that"
  * "That gets you laps — I don't care if it's raining"
  * "Try saying that during film review with Coach Wambs, see what happens"
  * "Go run it out with Coach Harrison's basketball squad if you've got that much energy"
  * "Principal Elliott doesn't tolerate that and neither do I" """

content = content.replace(old, new)
open('src/chat.py', 'w', encoding='utf-8').write(content)
print("done")
