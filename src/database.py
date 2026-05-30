"""SQLite / Turso database connection."""

import os
import sqlite3
from pathlib import Path
from config import DB_PATH

def get_conn():
    """Return a database connection — Turso HTTP in production, local SQLite in dev."""
    turso_url   = os.getenv("TURSO_URL")
    turso_token = os.getenv("TURSO_TOKEN")

    if turso_url and turso_token:
        return TursoHTTPConn(turso_url, turso_token)
    else:
        Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn


class _Row(dict):
    """sqlite3.Row-compatible dict with name and index access."""
    def __getitem__(self, key):
        if isinstance(key, int):
            return list(self.values())[key]
        return super().__getitem__(key)
    def keys(self):
        return list(super().keys())


class TursoHTTPCursor:
    def __init__(self, result):
        cols_raw = result.get("cols", result.get("columns", []))
        self._cols = [c.get("name", c) if isinstance(c, dict) else c for c in cols_raw]
        self._rows = result.get("rows", [])
        self._idx = 0

    def _parse_row(self, raw):
        values = []
        for cell in raw:
            if isinstance(cell, dict):
                values.append(None if cell.get("type") == "null" else cell.get("value"))
            else:
                values.append(cell)
        return _Row(zip(self._cols, values))

    def fetchone(self):
        if self._idx >= len(self._rows):
            return None
        row = self._parse_row(self._rows[self._idx])
        self._idx += 1
        return row

    def fetchall(self):
        return [self._parse_row(r) for r in self._rows[self._idx:]]

    def __iter__(self):
        return iter(self.fetchall())

    @property
    def description(self):
        return [(c, None, None, None, None, None, None) for c in self._cols]


class TursoHTTPConn:
    """sqlite3-compatible Turso connection using the HTTP pipeline API."""

    def __init__(self, url, token):
        import requests
        self._url = url.replace("libsql://", "https://")
        self._session = requests.Session()
        self._session.headers.update({
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        })

    def _run(self, sql, params=None):
        if params:
            for p in params:
                if p is None:
                    sql = sql.replace("?", "NULL", 1)
                elif isinstance(p, str):
                    sql = sql.replace("?", "'" + p.replace("'", "''") + "'", 1)
                else:
                    sql = sql.replace("?", str(p), 1)
        payload = {"requests": [{"type": "execute", "stmt": {"sql": sql}}, {"type": "close"}]}
        resp = self._session.post(f"{self._url}/v2/pipeline", json=payload, timeout=30)
        resp.raise_for_status()
        result = resp.json()
        r = result["results"][0]
        if r.get("type") == "error":
            raise Exception(r.get("error", {}).get("message", "Turso error"))
        return r.get("response", {}).get("result", {"cols": [], "rows": []})

    def execute(self, sql, params=None):
        return TursoHTTPCursor(self._run(sql, params))

    def executemany(self, sql, params_list):
        for params in params_list:
            self._run(sql, params)

    def executescript(self, script):
        for stmt in script.split(";"):
            stmt = stmt.strip()
            if stmt:
                try:
                    self._run(stmt)
                except Exception:
                    pass

    def commit(self):
        pass

    def close(self):
        pass

    @property
    def row_factory(self):
        return None

    @row_factory.setter
    def row_factory(self, v):
        pass


def init_db():
    conn = get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS league_lore (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            season      INTEGER,
            category    TEXT NOT NULL,
            title       TEXT NOT NULL,
            content     TEXT NOT NULL,
            tags        TEXT,
            created_at  INTEGER DEFAULT (strftime('%s','now'))
        );
    """)
    conn.commit()
    conn.close()
