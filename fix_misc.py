import re
content = open('templates/index.html', encoding='utf-8').read()

# 1. Remove border from action buttons, lighter color
old_share = """.share-btn{
      background:none;border:1px solid var(--border);color:var(--dim);
      font-family:"Oswald",sans-serif;font-size:.62rem;letter-spacing:1px;
      text-transform:uppercase;padding:4px 10px;border-radius:3px;cursor:pointer;
      display:flex;align-items:center;gap:5px;transition:.15s;
    }
    .share-btn:hover{ border-color:var(--gold);color:var(--gold); }
    .share-btn.copied{ border-color:#4caf50;color:#4caf50; }"""

new_share = """.share-btn{
      background:none;border:none;color:#444;
      font-family:"Oswald",sans-serif;font-size:.62rem;letter-spacing:1px;
      text-transform:uppercase;padding:4px 8px;border-radius:3px;cursor:pointer;
      display:flex;align-items:center;gap:5px;transition:.15s;
    }
    .share-btn:hover{ color:#aaa; }
    .share-btn.copied{ color:#4caf50; }"""

if old_share in content:
    content = content.replace(old_share, new_share)
    print("fixed share button style")
else:
    content = re.sub(r'\.share-btn\{[^}]+\}\s*\.share-btn:hover\{[^}]+\}\s*\.share-btn\.copied\{[^}]+\}', new_share, content)
    print("fixed share button style via regex")

# 2. Remove gold from table data - make all td text uniform
content = re.sub(
    r'(\.bubble tbody tr:first-child td:last-child\{color:var\(--pink\);\}\s*)',
    '',
    content
)
# Also remove any last-child gold styling
content = re.sub(r'\.bubble tbody td:last-child\{[^}]*color[^}]+\}', '', content)
print("removed gold from table data")

# 3. Smooth streaming - append text incrementally, only format on done
# Replace the streaming text update to use textContent append instead of innerHTML re-render
old_stream = """          fullText += event.chunk;
          bubble.innerHTML = formatText(fullText);
          bubble.closest('#chat-wrap').parentElement.scrollTop = 99999;"""

new_stream = """          fullText += event.chunk;
          // Append raw text during streaming for smoothness; format on done
          bubble.textContent = fullText;
          bubble.closest('#chat-wrap').parentElement.scrollTop = 99999;"""

if old_stream in content:
    content = content.replace(old_stream, new_stream)
    print("smoothed streaming")
else:
    print("WARNING: could not find streaming update code")

# Now update finalizeStreamBubble to do the full format render when done
old_finalize = "function finalizeStreamBubble(fullText) {"
new_finalize = """function finalizeStreamBubble(fullText) {
  // Now do the full markdown render
  const pendingBubble = document.querySelector('#stream-actions-pending')?.closest('.msg-col')?.querySelector('.bubble');
  if (pendingBubble) {
    pendingBubble.innerHTML = formatText(fullText);
  }"""

content = content.replace(old_finalize, new_finalize)
print("added full render on finalize")

open('templates/index.html', 'w', encoding='utf-8').write(content)
print("done")
