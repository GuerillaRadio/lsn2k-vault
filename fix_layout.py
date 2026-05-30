import re
content = open('templates/index.html', encoding='utf-8').read()

# Remove any old #suggestions grid CSS and add the correct new CSS
content = re.sub(r'#suggestions\{[^}]+\}', '', content)
content = re.sub(r'\.suggestions-fixed\{[^}]+\}', '', content)
content = re.sub(r'\.suggestions-recent\{[^}]+\}', '', content)
content = re.sub(r'\.suggestion-recent\{[^}]+\}', '', content)
content = re.sub(r'\.suggestion-recent [^{]+\{[^}]+\}', '', content)
content = re.sub(r'\.recent-icon\{[^}]+\}', '', content)

new_css = """
    #suggestions{
      display:flex;flex-direction:column;gap:9px;
      max-width:820px;width:100%;margin-top:26px;
    }
    .suggestions-fixed{
      display:grid;grid-template-columns:1fr 1fr;gap:9px;
    }
    .suggestions-recent{
      display:flex;flex-direction:column;gap:7px;
    }
    .suggestion-recent{
      display:flex;align-items:center;justify-content:space-between;
      width:100%;
    }
    .suggestion-recent .label{
      flex:1;text-align:left;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;
    }
    .recent-icon{
      color:var(--dim);font-size:.85rem;flex-shrink:0;margin-left:12px;
    }
"""

content = content.replace('  </style>', new_css + '  </style>')
open('templates/index.html', 'w', encoding='utf-8').write(content)
print("done")
