"""Push local SQLite to Turso using raw SQL with embedded values — no parameter types needed."""
import sqlite3, requests, sys
from pathlib import Path

TURSO_URL   = "https://lsn2k-guerillaradio.aws-us-east-2.turso.io"
TURSO_TOKEN = "eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9.eyJhIjoicnciLCJpYXQiOjE3ODAxNTE2MDksImlkIjoiMDE5ZTc5NDgtYWQwMS03ZmEyLWE4YzYtNDAyZjRkNWU2MTg0IiwicmlkIjoiODBiMjZkODUtOGI2MC00NWQwLWIyYTQtNDFlNmFiYWI0ODcwIn0.Pi0OoD5t8XuZp1Z45PaTX4ntJv3HuCWt0SWptoF9LOTSstbGw0MHa7PuWwK5SUJKCczKN6AC0EI87b3fs2XVAQ"
LOCAL_DB    = "data/fantasy.db"

HEADERS = {"Authorization": f"Bearer {TURSO_TOKEN}", "Content-Type": "application/json"}
SESSION = requests.Session()
SESSION.headers.update(HEADERS)

def sql_val(v):
    """Format a Python value as a SQL literal."""
    if v is None:
        return "NULL"
    if isinstance(v, (int, float)):
        return str(v)
    # Escape single quotes in strings
    return "'" + str(v).replace("'", "''") + "'"

def exec_sql(sql: str):
    payload = {"requests": [{"type": "execute", "stmt": {"sql": sql}}, {"type": "close"}]}
    resp = SESSION.post(f"{TURSO_URL}/v2/pipeline", json=payload, timeout=30)
    if not resp.ok:
        raise Exception(f"{resp.status_code}: {resp.text[:200]}")
    return resp.json()

def push_table(local, table, schema, rows, cols, batch_size=200):
    # Drop and recreate
    exec_sql(f"DROP TABLE IF EXISTS {table}")
    exec_sql(schema)

    if not rows:
        print(f"  {table}: empty")
        return

    col_names = ", ".join(cols)
    total = len(rows)

    for i in range(0, total, batch_size):
        batch = rows[i:i+batch_size]
        values = ", ".join(
            "(" + ", ".join(sql_val(v) for v in row) + ")"
            for row in batch
        )
        sql = f"INSERT OR IGNORE INTO {table} ({col_names}) VALUES {values}"
        try:
            exec_sql(sql)
        except Exception as e:
            print(f"  Batch {i//batch_size} error: {e}")
            # Fall back to row-by-row for this batch
            for row in batch:
                vals = "(" + ", ".join(sql_val(v) for v in row) + ")"
                try:
                    exec_sql(f"INSERT OR IGNORE INTO {table} ({col_names}) VALUES {vals}")
                except Exception as e2:
                    print(f"  Row error: {e2}")

        if i % 5000 == 0 and i > 0:
            print(f"  {table}: {i:,}/{total:,}...")

    print(f"  {table}: {total:,} rows done")

# Connect to local
local = sqlite3.connect(LOCAL_DB)
local.row_factory = sqlite3.Row

tables = [r[0] for r in local.execute(
    "SELECT name FROM sqlite_master WHERE type='table' AND name != 'sqlite_sequence' ORDER BY name"
).fetchall()]

print(f"Pushing {len(tables)} tables to Turso...\n")
exec_sql("PRAGMA foreign_keys=OFF")

for table in tables:
    schema = local.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name=?", (table,)
    ).fetchone()[0]
    rows = [tuple(r) for r in local.execute(f"SELECT * FROM {table}").fetchall()]
    cols = [d[0] for d in local.execute(f"SELECT * FROM {table} LIMIT 0").description]
    push_table(local, table, schema, rows, cols)

# Indexes
print("\nCreating indexes...")
for idx in local.execute("SELECT sql FROM sqlite_master WHERE type='index' AND sql IS NOT NULL").fetchall():
    try:
        exec_sql(idx[0])
    except:
        pass

# Verify
print("\nVerification:")
all_ok = True
for table in tables:
    local_n = local.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    try:
        result = exec_sql(f"SELECT COUNT(*) as n FROM {table}")
        remote_n = int(result["results"][0]["response"]["result"]["rows"][0][0]["value"])
        match = "OK" if local_n == remote_n else f"MISMATCH local={local_n:,} remote={remote_n:,}"
        if local_n != remote_n:
            all_ok = False
    except Exception as e:
        match = f"ERROR: {e}"
        all_ok = False
    print(f"  {table}: {local_n:,} [{match}]")

local.close()
print(f"\n{'All tables match!' if all_ok else 'Some mismatches — check above.'}")
