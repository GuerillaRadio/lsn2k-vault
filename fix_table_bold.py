content = open('templates/index.html', encoding='utf-8').read()

# Override strong/bold inside table cells to normal weight and color
css = """
    .bubble table strong{ color:var(--text);font-weight:400; }
    .bubble td strong, .bubble th strong{ color:inherit;font-weight:inherit; }
"""
content = content.replace('  </style>', css + '  </style>')
open('templates/index.html', 'w', encoding='utf-8').write(content)
print("done")
