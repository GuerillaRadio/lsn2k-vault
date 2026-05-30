content = open('templates/index.html', encoding='utf-8').read()

# Wrap logo and title in a clickable element that resets chat
old_brand = """  <div class="brand">
    <img src="/static/LSN2K_Logo.png" alt="LSN2K"/>
    <div>
      <h1>LSN2K Vault</h1>
      <div class="sub">League History &bull; Records</div>
    </div>
  </div>"""

new_brand = """  <div class="brand" onclick="resetChat()" style="cursor:pointer;" title="Back to home">
    <img src="/static/LSN2K_Logo.png" alt="LSN2K"/>
    <div>
      <h1>LSN2K Vault</h1>
      <div class="sub">League History &bull; Records</div>
    </div>
  </div>"""

content = content.replace(old_brand, new_brand)
open('templates/index.html', 'w', encoding='utf-8').write(content)
print("done")
