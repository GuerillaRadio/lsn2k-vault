import re

# 1. Fix mobile grid
content = open('templates/index.html', encoding='utf-8').read()

# Remove any existing suggestions-fixed mobile override and add a clean one
content = re.sub(r'\s*\.suggestions-fixed\{ grid-template-columns:1fr; \}\n', '\n', content)

# Add the override in the mobile media query — use a lower breakpoint (500px)
# so it triggers before cards overflow, and use !important to ensure it applies
mobile_add = '      .suggestions-fixed{ grid-template-columns:1fr !important; }\n'

# Find the mobile media query block and insert there
content = content.replace(
    '      .suggestions-recent .suggestion-recent:nth-child(n+3){ display:none; }',
    mobile_add + '      .suggestions-recent .suggestion-recent:nth-child(n+3){ display:none; }'
)

# Also add a tighter breakpoint that catches more devices
extra_breakpoint = """
    @media(max-width:700px){
      .suggestions-fixed{ grid-template-columns:1fr !important; }
    }
"""
content = content.replace('  </style>', extra_breakpoint + '  </style>')

open('templates/index.html', 'w', encoding='utf-8').write(content)
print("Fixed mobile grid")

# 2. Update system prompt for regular season player stats
content = open('src/chat.py', encoding='utf-8').read()

old = "**player_season_stats**"
# Only add if not already there
if "player_season_stats" not in content:
    new_table = """**player_season_stats** — PRE-COMPUTED player scoring per season. Use for ANY player point total question.
  player_key, player_name, position, nfl_team, season, league_key,
  reg_season_pts (REGULAR SEASON ONLY — default for all player scoring questions),
  playoff_pts, total_pts, weeks_started, weeks_benched, best_week_pts, best_week, worst_week_pts

  DEFAULT BEHAVIOR: When asked about player points/scoring, ALWAYS use reg_season_pts unless playoffs are explicitly requested.
  Always note to the user that figures are regular season only.
  Top QB in 2022: SELECT player_name, reg_season_pts FROM player_season_stats WHERE season=2022 AND position='QB' AND weeks_started>=6 ORDER BY reg_season_pts DESC LIMIT 1

"""
    content = content.replace("**trade_summary**", new_table + "**trade_summary**")
    open('src/chat.py', 'w', encoding='utf-8').write(content)
    print("Updated system prompt with player_season_stats")
else:
    print("player_season_stats already in prompt")
