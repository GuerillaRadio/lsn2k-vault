content = open('templates/index.html', encoding='utf-8').read()

# Revert to innerHTML with formatText but throttled via requestAnimationFrame
content = content.replace(
    'bubble.textContent = fullText;',
    """if (!bubble._rafPending) {
            bubble._rafPending = true;
            requestAnimationFrame(() => {
              bubble.innerHTML = formatText(fullText);
              bubble._rafPending = false;
            });
          }"""
)

open('templates/index.html', 'w', encoding='utf-8').write(content)
print("done")
