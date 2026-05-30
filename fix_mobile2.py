import re
content = open('templates/index.html', encoding='utf-8').read()

# Fix mobile CSS - logo closer to top, more space around coach row, limit suggestions
old_mobile = """      #landing{ padding:16px 14px 12px;gap:0; }
      .logo-hero{ width:min(280px,80vw);margin-bottom:20px; }
      .coach-row{ gap:12px;max-width:100%; }
      .coach-face{ width:60px; }
      .coach-copy h2{ font-size:1.1rem; }
      .coach-copy p{ font-size:.8rem;margin-top:5px; }

      #suggestions{
        grid-template-columns:1fr;gap:7px;margin-top:18px;
        max-height:38vh;overflow-y:auto;
      }"""

new_mobile = """      #landing{ padding:8px 14px 12px;gap:0;justify-content:flex-start; }
      .logo-hero{ width:min(260px,75vw);margin-bottom:0;margin-top:8px; }
      .coach-row{ gap:12px;max-width:100%;margin:24px 0; }
      .coach-face{ width:60px; }
      .coach-copy h2{ font-size:1.1rem; }
      .coach-copy p{ font-size:.8rem;margin-top:5px; }

      #suggestions{
        grid-template-columns:1fr;gap:7px;margin-top:0;
      }
      #suggestions .suggestion:nth-child(n+3){ display:none; }"""

if old_mobile in content:
    content = content.replace(old_mobile, new_mobile)
    print("replaced mobile CSS")
else:
    print("WARNING: could not find mobile CSS block, trying regex")
    content = re.sub(
        r'#landing\{ padding:16px[^}]+\}',
        '#landing{ padding:8px 14px 12px;gap:0;justify-content:flex-start; }',
        content
    )

open('templates/index.html', 'w', encoding='utf-8').write(content)
print("done")
