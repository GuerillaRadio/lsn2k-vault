import re
content = open('templates/index.html', encoding='utf-8').read()

# Add user nameplate CSS
old_nameplate = """.nameplate{
      font-family:"Oswald",sans-serif;font-size:.72rem;letter-spacing:1.5px;
      text-transform:uppercase;color:var(--pink);font-weight:600;
    }
    .nameplate b{color:var(--dim);font-weight:500;margin-left:8px;letter-spacing:1px;}"""

new_nameplate = """.nameplate{
      font-family:"Oswald",sans-serif;font-size:.72rem;letter-spacing:1.5px;
      text-transform:uppercase;color:var(--gold);font-weight:600;
    }
    .nameplate b{color:var(--dim);font-weight:500;margin-left:8px;letter-spacing:1px;}
    .nameplate.user-nameplate{color:var(--muted);}"""

content = content.replace(old_nameplate, new_nameplate)

# In the JS addMessage function, add a nameplate above user bubbles too
content = content.replace(
    """  if (role === 'assistant'){
    const np = document.createElement('div');
    np.className = 'nameplate';
    np.innerHTML = 'Coach Taylor';
    col.appendChild(np);
  }""",
    """  const np = document.createElement('div');
  np.className = role === 'assistant' ? 'nameplate' : 'nameplate user-nameplate';
  np.textContent = role === 'assistant' ? 'Coach Taylor' : 'You';
  col.appendChild(np);"""
)

# Same fix in createStreamBubble
content = content.replace(
    """  np.innerHTML = 'Coach Taylor';""",
    """  np.textContent = 'Coach Taylor';"""
)

open('templates/index.html', 'w', encoding='utf-8').write(content)
print("done")
