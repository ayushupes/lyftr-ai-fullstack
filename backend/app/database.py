import os
import sqlite3
import json
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from app.config import settings

def parse_sqlite_path(db_url: str) -> str:
    """Parse sqlite db file path from DATABASE_URL."""
    prefix = "sqlite:///"
    if db_url.startswith(prefix):
        path = db_url[len(prefix):]
    else:
        path = db_url

    # In unix/docker, sqlite:////data/app.db stripped of sqlite:/// gives /data/app.db
    # On windows, sqlite:///./app.db gives ./app.db
    if not path:
        path = "app.db"
    return path

def get_db_path() -> str:
    return parse_sqlite_path(settings.DATABASE_URL)

def get_db_connection() -> sqlite3.Connection:
    db_path = get_db_path()
    # Ensure directory exists if path contains directory separator
    dirname = os.path.dirname(db_path)
    if dirname:
        try:
            os.makedirs(dirname, exist_ok=True)
        except OSError:
            pass

    conn = sqlite3.connect(db_path, timeout=10.0, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn

def init_db():
    """Create schema on startup if not exists."""
    conn = get_db_connection()
    try:
        with conn:
            conn.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                metadata TEXT,
                created_at TEXT NOT NULL
            );
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_messages_session_id ON messages (session_id);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages (created_at);")
    finally:
        conn.close()

def check_db_health() -> bool:
    """Check if the SQLite database is reachable."""
    try:
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT 1;")
            cur.fetchone()
            return True
        finally:
            conn.close()
    except Exception:
        return False

def get_session_messages(session_id: str) -> List[Dict[str, Any]]:
    """Retrieve all messages for a session, ordered oldest first."""
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, session_id, role, content, metadata, created_at FROM messages WHERE session_id = ? ORDER BY id ASC;",
            (session_id,)
        )
        rows = cur.fetchall()
        result = []
        for row in rows:
            meta = None
            if row["metadata"]:
                try:
                    meta = json.loads(row["metadata"])
                except Exception:
                    meta = None
            result.append({
                "id": row["id"],
                "session_id": row["session_id"],
                "role": row["role"],
                "content": row["content"],
                "metadata": meta,
                "created_at": row["created_at"]
            })
        return result
    finally:
        conn.close()

def save_chat_turn(
    session_id: str,
    user_content: str,
    assistant_content: str,
    assistant_metadata: Dict[str, Any]
) -> None:
    """Save both user message and assistant message in a single transaction."""
    conn = get_db_connection()
    try:
        now_iso = datetime.now(timezone.utc).isoformat()
        # Filter metadata for storage in messages table:
        # As per PDF GET /sessions/{session_id}/messages response:
        # { "resolution_source": "LIVE_INFERENCE", "input_tokens": 42, "output_tokens": 9 }
        storage_meta = {
            "resolution_source": assistant_metadata.get("resolution_source"),
            "input_tokens": assistant_metadata.get("input_tokens"),
            "output_tokens": assistant_metadata.get("output_tokens")
        }
        meta_json = json.dumps(storage_meta)

        with conn:
            conn.execute(
                "INSERT INTO messages (session_id, role, content, metadata, created_at) VALUES (?, ?, ?, ?, ?);",
                (session_id, "user", user_content, None, now_iso)
            )
            conn.execute(
                "INSERT INTO messages (session_id, role, content, metadata, created_at) VALUES (?, ?, ?, ?, ?);",
                (session_id, "assistant", assistant_content, meta_json, now_iso)
            )
    finally:
        conn.close()
