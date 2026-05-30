import re
content = open('templates/index.html', encoding='utf-8').read()

# 1. Fix table overflow in bubbles
table_fix = """
    .bubble table{ max-width:100%;overflow-x:auto;display:block; }
    .bubble table thead,.bubble table tbody,.bubble table tr{ display:table;width:100%;table-layout:fixed; }
"""

# 2. Fix input area on mobile - prevent viewport zoom/shift when keyboard opens
mobile_input_fix = """
    @media(max-width:640px){
      #input-area{ position:sticky;bottom:0;z-index:100; }
      #user-input{ font-size:16px !important; }
      #input-row{ flex-wrap:nowrap;align-items:flex-end; }
      #send-btn{ flex-shrink:0;min-width:42px; }
    }
"""

content = content.replace('  </style>', table_fix + mobile_input_fix + '  </style>')
open('templates/index.html', 'w', encoding='utf-8').write(content)
print("done")
