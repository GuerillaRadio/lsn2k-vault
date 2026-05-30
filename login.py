"""Run this once to authorize with Yahoo and verify the connection."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from auth import get_oauth, FANTASY_BASE


def test_connection():
    oauth = get_oauth()
    resp = oauth.session.get(
        f"{FANTASY_BASE}/users;use_login=1/games",
        params={"format": "json"},
    )
    if resp.status_code == 200:
        data = resp.json()
        games = (
            data.get("fantasy_content", {})
            .get("users", {})
            .get("0", {})
            .get("user", [{}])[1]
            .get("games", {})
        )
        count = games.get("count", 0)
        print(f"\nConnection successful! Found {count} Yahoo Fantasy game(s) on your account.")
        for i in range(count):
            entry = games.get(str(i), {})
            game = entry.get("game", [{}])
            g = game[0] if isinstance(game, list) else game
            print(f"  - {g.get('name')} ({g.get('season')}) — key: {g.get('game_key')}")
    else:
        print(f"Error {resp.status_code}: {resp.text}")


if __name__ == "__main__":
    test_connection()
