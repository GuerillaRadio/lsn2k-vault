content = open('templates/index.html', encoding='utf-8').read()
# The recent buttons no longer have .recent-label class on the span - let me verify
import re
# Check what the recent buttons look like now and fix the JS selector if needed
# The label span should still have class "label recent-label"
print("Recent button 0:", re.search(r'id="recent-0"[^>]*>.*?</button>', content, re.DOTALL).group(0)[:200])
