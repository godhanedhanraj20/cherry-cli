import os
import sqlite3
import time
from typing import Any

CONFIG_DIR = os.path.expanduser("~/.tsg-cli")
SESSION_DB_FILE = os.path.join(CONFIG_DIR, "auth_sessions.db")



def _ensure_config_dir():
    os.makedirs(CONFIG_DIR, exist_ok=True)



def _connect() -> sqlite3.Connection:
    _ensure_config_dir()
    conn = sqlite3.connect(SESSION_DB_FILE)
    conn.row_factory = sqlite3.Row
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS sessions (
          session_id TEXT PRIMARY KEY,
          api_id INTEGER,
          api_hash TEXT,
          phone_number TEXT,
          phone_code_hash TEXT,
          state TEXT,
          created_at REAL,
          two_fa_attempts INTEGER
        )
        """
    )
    conn.commit()
    return conn



def create_session(
    session_id: str,
    api_id: int,
    api_hash: str,
    phone_number: str,
    phone_code_hash: str,
    state: str,
    created_at: float,
    two_fa_attempts: int = 0,
):
    with _connect() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO sessions
            (session_id, api_id, api_hash, phone_number, phone_code_hash, state, created_at, two_fa_attempts)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (session_id, api_id, api_hash, phone_number, phone_code_hash, state, created_at, two_fa_attempts),
        )
        conn.commit()



def get_session(session_id: str) -> dict[str, Any] | None:
    with _connect() as conn:
        row = conn.execute("SELECT * FROM sessions WHERE session_id = ?", (session_id,)).fetchone()
        if not row:
            return None
        return dict(row)



def update_session(session_id: str, **fields: Any):
    if not fields:
        return
    columns = ", ".join([f"{k} = ?" for k in fields.keys()])
    values = list(fields.values())
    values.append(session_id)
    with _connect() as conn:
        conn.execute(f"UPDATE sessions SET {columns} WHERE session_id = ?", values)
        conn.commit()



def delete_session(session_id: str):
    with _connect() as conn:
        conn.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
        conn.commit()



def cleanup_expired_sessions(ttl_seconds: int) -> int:
    threshold = time.time() - ttl_seconds
    with _connect() as conn:
        cur = conn.execute("DELETE FROM sessions WHERE created_at < ?", (threshold,))
        conn.commit()
        return int(cur.rowcount or 0)



def count_sessions() -> int:
    with _connect() as conn:
        row = conn.execute("SELECT COUNT(*) AS c FROM sessions").fetchone()
        return int(row["c"] if row else 0)
