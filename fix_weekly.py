content = open('weekly_update.py', encoding='utf-8').read()
old = 'subprocess.run([sys.executable, str(Path(__file__).parent / "build_final_standings.py")])'
new = '''subprocess.run([sys.executable, str(Path(__file__).parent / "build_final_standings.py")])
subprocess.run([sys.executable, str(Path(__file__).parent / "rebuild_trade_summary.py")])
subprocess.run([sys.executable, str(Path(__file__).parent / "build_all_analytics.py")])'''
content = content.replace(old, new)
open('weekly_update.py', 'w', encoding='utf-8').write(content)
print("done")
