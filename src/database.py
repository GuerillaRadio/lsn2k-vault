"""SQLite / Turso database connection."""

import os
import sqlite3
from pathlib import Path
from config import DB_PATH

TURSO_URL   = os.getenv("TURSO_URL")
TURSO_TOKEN = os.getenv("TURSO_TOKEN")


def get_conn():
    """Return a database connection — Turso in production, local SQLite in dev."""
    if TURSO_URL and TURSO_TOKEN:
        import libsql_experimental as libsql
        conn = libsql.connect(TURSO_URL, auth_token=TURSO_TOKEN)
        conn.row_factory = sqlite3.Row
        return conn
    else:
        Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn


class TursoHTTPConn:
    """Minimal sqlite3-compatible wrapper using Turso HTTP API."""
    import requests as _requests

    def __init__(self, url, token):
        self._url = url.replace("libsql://", "https://")
        self._headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    def _exec(self, sql, params=None):
        import requests
        if params:
            # Simple param substitution
            for p in params:
                if p is None:
                    sql = sql.replace("?", "NULL", 1)
                elif isinstance(p, str):
                    sql = sql.replace("?", "'" + p.replace("'", "''") + "'", 1)
                else:
                    sql = sql.replace("?", str(p), 1)
        payload = {"requests": [{"type": "execute", "stmt": {"sql": sql}}, {"type": "close"}]}
        resp = requests.post(f"{self._url}/v2/pipeline", headers=self._headers, json=payload, timeout=30)
        resp.raise_for_status()
        return resp.json()["results"][0]["response"]["result"]

    def execute(self, sql, params=None):
        result = self._exec(sql, params)
        return TursoHTTPCursor(result)

    def executemany(self, sql, params_list):
        for params in params_list:
            self._exec(sql, params)
        return self

    def executescript(self, script):
        for stmt in script.split(";"):
            stmt = stmt.strip()
            if stmt:
                try:
                    self._exec(stmt)
                except:
                    pass
        return self

    def commit(self):
        pass

    def close(self):
        pass

    @property
    def row_factory(self):
        return sqlite3.Row

    @row_factory.setter
    def row_factory(self, v):
        pass


class TursoHTTPCursor:
    def __init__(self, result):
        self._result = result
        self._rows = result.get("rows", [])
        self._cols = [c["name"] for c in result.get("columns", [])]
        self._idx = 0

    def fetchone(self):
        if self._idx >= len(self._rows):
            return None
        row = self._make_row(self._rows[self._idx])
        self._idx += 1
        return row

    def fetchall(self):
        return [self._make_row(r) for r in self._rows]

    def _make_row(self, raw_row):
        values = [c.get("value") if c.get("type") != "null" else None for c in raw_row]
        return sqlite3.Row.__new__(sqlite3.Row)  # Can't easily subclass; use dict
        # Fall back to plain tuple with dict-like access
        return _DictRow(dict(zip(self._cols, values)))

    def __iter__(self):
        return iter(self.fetchall())

    @property
    def description(self):
        return [(c, None, None, None, None, None, None) for c in self._cols]


class _DictRow(dict):
    def __getitem__(self, key):
        if isinstance(key, int):
            return list(self.values())[key]
        return super().__getitem__(key)


def init_db():
    conn = get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS leagues (
            league_key          TEXT PRIMARY KEY,
            season              INTEGER NOT NULL,
            name                TEXT,
            num_teams           INTEGER,
            scoring_type        TEXT,
            start_week          INTEGER,
            end_week            INTEGER,
            start_date          TEXT,
            end_date            TEXT,
            current_week        INTEGER,
            is_finished         INTEGER DEFAULT 0,
            playoff_start_week  INTEGER,
            num_playoff_teams   INTEGER,
            waiver_type         TEXT,
            waiver_rule         TEXT,
            trade_end_date      TEXT,
            trade_ratify_type   TEXT,
            game_key            TEXT
        );

        CREATE TABLE IF NOT EXISTS teams (
            team_key            TEXT PRIMARY KEY,
            league_key          TEXT NOT NULL,
            season              INTEGER NOT NULL,
            team_id             INTEGER,
            name                TEXT,
            manager_name        TEXT,
            manager_guid        TEXT,
            waiver_priority     INTEGER,
            draft_grade         TEXT,
            draft_recap_url     TEXT,
            logo_url            TEXT,
            clinched_playoffs   INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS standings (
            team_key            TEXT NOT NULL,
            league_key          TEXT NOT NULL,
            season              INTEGER NOT NULL,
            rank                INTEGER,
            playoff_seed        INTEGER,
            wins                INTEGER,
            losses              INTEGER,
            ties                INTEGER,
            points_for          REAL,
            points_against      REAL,
            streak_type         TEXT,
            streak_length       INTEGER,
            PRIMARY KEY (team_key, league_key)
        );

        CREATE TABLE IF NOT EXISTS roster_positions (
            league_key          TEXT NOT NULL,
            position            TEXT NOT NULL,
            count               INTEGER DEFAULT 1,
            position_type       TEXT,
            PRIMARY KEY (league_key, position)
        );

        CREATE TABLE IF NOT EXISTS scoring_settings (
            league_key          TEXT NOT NULL,
            stat_id             TEXT NOT NULL,
            stat_name           TEXT,
            value               REAL,
            bonus_type          TEXT,
            PRIMARY KEY (league_key, stat_id)
        );

        CREATE TABLE IF NOT EXISTS stat_categories (
            game_key            TEXT NOT NULL,
            stat_id             TEXT NOT NULL,
            name                TEXT,
            display_name        TEXT,
            sort_order          TEXT,
            position_type       TEXT,
            PRIMARY KEY (game_key, stat_id)
        );

        CREATE TABLE IF NOT EXISTS matchups (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            league_key          TEXT NOT NULL,
            season              INTEGER NOT NULL,
            week                INTEGER NOT NULL,
            team1_key           TEXT NOT NULL,
            team2_key           TEXT,
            team1_points        REAL,
            team2_points        REAL,
            team1_projected     REAL,
            team2_projected     REAL,
            winner_team_key     TEXT,
            is_playoffs         INTEGER DEFAULT 0,
            is_consolation      INTEGER DEFAULT 0,
            is_bye              INTEGER DEFAULT 0,
            UNIQUE (league_key, week, team1_key)
        );

        CREATE TABLE IF NOT EXISTS draft_picks (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            league_key          TEXT NOT NULL,
            season              INTEGER NOT NULL,
            round               INTEGER,
            pick                INTEGER,
            team_key            TEXT,
            player_key          TEXT,
            UNIQUE (league_key, round, pick)
        );

        CREATE TABLE IF NOT EXISTS players (
            player_key          TEXT PRIMARY KEY,
            name                TEXT,
            first_name          TEXT,
            last_name           TEXT,
            position            TEXT,
            nfl_team            TEXT,
            jersey_number       TEXT,
            status              TEXT
        );

        CREATE TABLE IF NOT EXISTS roster_slots (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            league_key          TEXT NOT NULL,
            team_key            TEXT NOT NULL,
            season              INTEGER NOT NULL,
            week                INTEGER NOT NULL,
            player_key          TEXT NOT NULL,
            selected_position   TEXT,
            is_starting         INTEGER DEFAULT 1,
            UNIQUE (team_key, week, player_key)
        );

        CREATE TABLE IF NOT EXISTS player_weekly_stats (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            league_key          TEXT NOT NULL,
            player_key          TEXT NOT NULL,
            season              INTEGER NOT NULL,
            week                INTEGER NOT NULL,
            fantasy_points      REAL,
            stats_json          TEXT,
            UNIQUE (league_key, player_key, season, week)
        );

        CREATE TABLE IF NOT EXISTS transactions (
            transaction_key     TEXT PRIMARY KEY,
            league_key          TEXT NOT NULL,
            season              INTEGER NOT NULL,
            type                TEXT,
            status              TEXT,
            timestamp           INTEGER,
            faab_bid            INTEGER,
            trader_team_key     TEXT,
            tradee_team_key     TEXT
        );

        CREATE TABLE IF NOT EXISTS transaction_players (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            transaction_key     TEXT NOT NULL,
            player_key          TEXT NOT NULL,
            player_name         TEXT,
            position            TEXT,
            nfl_team            TEXT,
            transaction_type    TEXT,
            source_team_key     TEXT,
            dest_team_key       TEXT,
            source_type         TEXT,
            dest_type           TEXT
        );

        CREATE TABLE IF NOT EXISTS owners (
            owner_id            INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name           TEXT NOT NULL,
            nickname            TEXT,
            yahoo_names         TEXT,
            franchise_name      TEXT
        );

        CREATE TABLE IF NOT EXISTS team_owner_map (
            team_key            TEXT PRIMARY KEY,
            owner_id            INTEGER
        );

        CREATE TABLE IF NOT EXISTS championships (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            season              INTEGER NOT NULL,
            owner_id            INTEGER NOT NULL,
            note                TEXT,
            UNIQUE(season, owner_id)
        );

        CREATE TABLE IF NOT EXISTS owner_season_stats (
            owner_id            INTEGER NOT NULL,
            season              INTEGER NOT NULL,
            team_name           TEXT,
            franchise_name      TEXT,
            wins                INTEGER DEFAULT 0,
            losses              INTEGER DEFAULT 0,
            ties                INTEGER DEFAULT 0,
            points_for          REAL DEFAULT 0,
            points_against      REAL DEFAULT 0,
            playoff_seed        INTEGER,
            made_playoffs       INTEGER DEFAULT 0,
            final_rank          INTEGER,
            won_championship    INTEGER DEFAULT 0,
            PRIMARY KEY (owner_id, season)
        );

        CREATE TABLE IF NOT EXISTS owner_all_time (
            owner_id            INTEGER PRIMARY KEY,
            nickname            TEXT,
            full_name           TEXT,
            franchise_name      TEXT,
            seasons_played      INTEGER DEFAULT 0,
            total_wins          INTEGER DEFAULT 0,
            total_losses        INTEGER DEFAULT 0,
            total_ties          INTEGER DEFAULT 0,
            total_points_for    REAL DEFAULT 0,
            total_points_against REAL DEFAULT 0,
            win_pct             REAL DEFAULT 0,
            playoff_appearances INTEGER DEFAULT 0,
            championships       INTEGER DEFAULT 0,
            runner_up           INTEGER DEFAULT 0,
            best_season_wins    INTEGER DEFAULT 0,
            best_season_year    INTEGER,
            highest_score       REAL DEFAULT 0,
            highest_score_week  INTEGER,
            highest_score_year  INTEGER
        );

        CREATE TABLE IF NOT EXISTS owner_h2h (
            owner1_id           INTEGER NOT NULL,
            owner2_id           INTEGER NOT NULL,
            wins                INTEGER DEFAULT 0,
            losses              INTEGER DEFAULT 0,
            ties                INTEGER DEFAULT 0,
            points_for          REAL DEFAULT 0,
            points_against      REAL DEFAULT 0,
            PRIMARY KEY (owner1_id, owner2_id)
        );

        CREATE TABLE IF NOT EXISTS weekly_high_scores (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            season              INTEGER,
            week                INTEGER,
            owner_id            INTEGER,
            team_key            TEXT,
            score               REAL,
            is_playoffs         INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS response_cache (
            question_hash       TEXT PRIMARY KEY,
            question            TEXT NOT NULL,
            answer              TEXT NOT NULL,
            created_at          INTEGER DEFAULT (strftime('%s','now')),
            hit_count           INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS response_ratings (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            rating              INTEGER,
            response_preview    TEXT,
            created_at          INTEGER DEFAULT (strftime('%s','now'))
        );

        CREATE INDEX IF NOT EXISTS idx_matchups_league_week   ON matchups(league_key, week);
        CREATE INDEX IF NOT EXISTS idx_standings_season       ON standings(season);
        CREATE INDEX IF NOT EXISTS idx_roster_team_week       ON roster_slots(team_key, week);
        CREATE INDEX IF NOT EXISTS idx_stats_player_season    ON player_weekly_stats(player_key, season);
        CREATE INDEX IF NOT EXISTS idx_tx_league              ON transactions(league_key);
        CREATE INDEX IF NOT EXISTS idx_txp_player             ON transaction_players(player_key);
        CREATE INDEX IF NOT EXISTS idx_draft_player           ON draft_picks(player_key);
    """)
    conn.commit()
    conn.close()
    print("Database initialized.")


if __name__ == "__main__":
    init_db()
