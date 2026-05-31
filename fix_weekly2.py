content = open('weekly_update.py', encoding='utf-8').read()
old = 'subprocess.run([sys.executable, str(Path(__file__).parent / "build_all_analytics.py")])'
new = ('subprocess.run([sys.executable, str(Path(__file__).parent / "build_all_analytics.py")])\n'
       'subprocess.run([sys.executable, str(Path(__file__).parent / "build_player_season_stats.py")])')
content = content.replace(old, new)
open('weekly_update.py', 'w', encoding='utf-8').write(content)
print("done")
