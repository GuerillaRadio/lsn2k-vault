content = open('src/chat.py', encoding='utf-8').read()
content = content.replace('MODEL = "claude-haiku-4-5"', 'MODEL = "claude-sonnet-4-6"')
open('src/chat.py', 'w', encoding='utf-8').write(content)
print("done")
