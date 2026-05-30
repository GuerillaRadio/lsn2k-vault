import re
content = open('templates/index.html', encoding='utf-8').read()

# 1. Headers: Roboto, not Oswald, not all-caps
content = re.sub(
    r'(\.bubble h2,\.bubble h3,\.bubble h4\{)[^}]+\}',
    r'\1font-family:"Roboto",sans-serif;font-weight:700;letter-spacing:0;color:#fff;margin:1.1em 0 .5em;}',
    content
)
content = re.sub(r'\.bubble h2\{font-size:1\.15rem;\}', '.bubble h2{font-size:1.1rem;}', content)
content = re.sub(r'\.bubble h3\{font-size:1\.02rem;\}', '.bubble h3{font-size:1rem;}', content)
content = re.sub(r'\.bubble h4\{font-size:\.9rem;color:var\(--pink\);\}', '.bubble h4{font-size:.92rem;color:#ccc;}', content)

# Also fix the formatText headers to not use Oswald color
content = content.replace(
    """'<h4 style="color:#c4b5fd;margin:.5em 0 .3em">$1</h4>'""",
    """'<h4>$1</h4>'"""
)
content = content.replace(
    """'<h3 style="color:#c4b5fd;margin:.6em 0 .3em">$1</h3>'""",
    """'<h3>$1</h3>'"""
)
content = content.replace(
    """'<h2 style="color:#a78bfa;margin:.7em 0 .3em">$1</h2>'""",
    """'<h2>$1</h2>'"""
)

# 2. More paragraph spacing
content = re.sub(
    r'\.bubble p\{margin-bottom:[^;]+;?\}',
    '.bubble p{margin-bottom:1.1em;}',
    content
)

# 3. More table margin
content = re.sub(
    r'(\.bubble table\{[^}]*?)margin:[^;]+em 0[^;]*;',
    r'\1margin:1.6em 0;',
    content
)

open('templates/index.html', 'w', encoding='utf-8').write(content)
print("done")
