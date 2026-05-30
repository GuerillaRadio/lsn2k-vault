"""Push local SQLite to Turso via HTTP API — no native libraries needed."""
import sqlite3, json, requests, sys
from pathlib import Path

TURSO_URL   = "https://lsn2k-guerillaradio.aws-us-east-2.turso.io"
TURSO_TOKEN = "eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9.eyJhIjoicnciLCJpYXQiOjE3ODAxNTE2MDksImlkIjoiMDE5ZTc5NDgtYWQwMS03ZmEyLWE4YzYtNDAyZjRkNWU2MTg0IiwicmlkIjoiODBiMjZkODUtOGI2MC00NWQwLWIyYTQtNDFlNmFiYWI0ODcwIn0.Pi0OoD5t8XuZp1Z45PaTX4ntJv3HuCWt0SWptoF9LOTSstbGw0MHa7PuWwK5SUJKCczKN6AC0EI87b3fs2XVAQ"
LOCAL_DB    = "data/fantasy.db"

HEADERS = {
    "Authorization": f"Bearer {TURSO_TOKEN}",
    "Content-Type": "application/json",
}

def execute(statements: list[dict]) -> dict:
    """Execute a batch of SQL statements via Turso HTTP API."""
    payload = {"requests": [{"type": "execute", "stmt": s} for s in statements]
               + [{"type": "close"}]}
    resp = requests.post(f"{TURSO_URL}/v2/pipeline", headers=HEADERS, json=payload, timeout=30)
    resp.raise_for_status()
    return resp.json()

def run_sql(sql: str, args: list = None):
    stmt = {"sql": sql}
    if args:
        stmt["args"] = [{"type": "text", "value": str(a)} if a is not None else {"type": "null"} for a in args]
    result = execute([stmt])
    return result

def make_arg(v):
    if v is None:
        return {"type": "null"}
    if isinstance(v, bool):
        return {"type": "integer", "value": str(int(v))}
    if isinstance(v, int):
        return {"type": "integer", "value": str(v)}
    if isinstance(v, float):
        return {"type": "float", "value": str(v)}
    s = str(v)
    return {"type": "text", "value": s}

def run_many(sql: str, rows: list, batch_size: int = 25):
    for i in range(0, len(rows), batch_size):
        batch = rows[i:i+batch_size]
        stmts = [{"sql": sql, "args": [make_arg(v) for v in row]} for row in batch]
        try:
            execute(stmts)
        except requests.exceptions.HTTPError as e:
            print(f"\n  Batch error at row {i}: {e.response.text[:300]}")
            # Try one at a time to find bad row
            for j, row in enumerate(batch):
                try:
                    execute([{"sql": sql, "args": [make_arg(v) for v in row]}])
                except Exception as e2:
                    print(f"  Bad row {i+j}: {row[:3]}... error: {e2}")
                    continue

# Connect to local DB
local = sqlite3.connect(LOCAL_DB)
local.row_factory = sqlite3.Row

tables = [r[0] for r in local.execute(
    "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
).fetchall()]
print(f"Pushing {len(tables)} tables to Turso...\n")

for table in tables:
    schema = local.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name=?", (table,)
    ).fetchone()[0]

    rows = local.execute(f"SELECT * FROM {table}").fetchall()
    cols = [d[0] for d in local.execute(f"SELECT * FROM {table} LIMIT 0").description]
    total = len(rows)

    # Drop, recreate, insert
    try:
        run_sql(f"DROP TABLE IF EXISTS {table}")
    except: pass

    try:
        run_sql(schema)
    except Exception as e:
        print(f"  {table}: schema failed — {e}")
        continue

    if total == 0:
        print(f"  {table}: empty")
        continue

    placeholders = ",".join(["?" for _ in cols])
    col_names = ",".join(cols)
    insert_sql = f"INSERT OR IGNORE INTO {table} ({col_names}) VALUES ({placeholders})"

    row_tuples = [tuple(r) for r in rows]
    run_many(insert_sql, row_tuples, batch_size=50)
    print(f"  {table}: {total:,} rows")

# Indexes
print("\nCreating indexes...")
for idx in local.execute("SELECT sql FROM sqlite_master WHERE type='index' AND sql IS NOT NULL").fetchall():
    try: run_sql(idx[0])
    except: pass

# Verify
print("\nVerification:")
for table in tables:
    local_n = local.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    try:
        result = execute([{"sql": f"SELECT COUNT(*) as n FROM {table}"}])
        remote_n = int(result["results"][0]["response"]["result"]["rows"][0][0]["value"])
        match = "OK" if local_n == remote_n else f"MISMATCH local={local_n} remote={remote_n}"
    except Exception as e:
        match = f"CHECK FAILED: {e}"
    print(f"  {table}: {local_n:,} [{match}]")

local.close()
print("\nDone!")
