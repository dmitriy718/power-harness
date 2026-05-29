import json
import os
import sqlite3
from pathlib import Path
from datetime import datetime, timezone
from typing import Any

DB_PATH = Path(os.environ.get("DATABASE_URL", "sqlite:///./data/nova_agent.db").replace("sqlite://", ""))
DB_DIR = DB_PATH.parent

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT, meta TEXT);
CREATE TABLE IF NOT EXISTS projects (id INTEGER PRIMARY KEY, name TEXT, meta TEXT);
CREATE TABLE IF NOT EXISTS conversations (id INTEGER PRIMARY KEY, project_id INTEGER, title TEXT, created_at TEXT);
CREATE TABLE IF NOT EXISTS messages (id INTEGER PRIMARY KEY, conversation_id INTEGER, role TEXT, content TEXT, created_at TEXT);
CREATE TABLE IF NOT EXISTS memories (id INTEGER PRIMARY KEY, project_id INTEGER, kind TEXT, content TEXT, score REAL, created_at TEXT, source TEXT, confidence REAL, archived INTEGER DEFAULT 0);
CREATE TABLE IF NOT EXISTS tasks (id INTEGER PRIMARY KEY, uuid TEXT, project_id INTEGER, user_id INTEGER, status TEXT, spec TEXT, created_at TEXT, updated_at TEXT);
CREATE TABLE IF NOT EXISTS task_events (id INTEGER PRIMARY KEY, task_id INTEGER, event_type TEXT, payload TEXT, created_at TEXT);
CREATE TABLE IF NOT EXISTS tool_calls (id INTEGER PRIMARY KEY, task_id INTEGER, tool TEXT, input TEXT, output TEXT, created_at TEXT);
CREATE TABLE IF NOT EXISTS artifacts (id INTEGER PRIMARY KEY, task_id INTEGER, path TEXT, meta TEXT, created_at TEXT);
CREATE TABLE IF NOT EXISTS file_index (id INTEGER PRIMARY KEY, project_id INTEGER, path TEXT, chunk TEXT, created_at TEXT);
CREATE TABLE IF NOT EXISTS repo_summaries (id INTEGER PRIMARY KEY, project_id INTEGER, summary TEXT, created_at TEXT);
"""


def init_db():
    DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()
    cur.executescript(SCHEMA)
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()

# Ensure DB initialized on import (helps tests and first-run)
try:
    init_db()
except Exception:
    pass


def _get_conn():
    DB_DIR.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(str(DB_PATH), check_same_thread=False)


def insert_task(uuid: str, project_id: int, user_id: int, status: str, spec: str):
    conn = _get_conn()
    cur = conn.cursor()
    now = datetime.now(timezone.utc).isoformat()
    cur.execute(
        "INSERT INTO tasks (uuid, project_id, user_id, status, spec, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (uuid, project_id, user_id, status, spec, now, now),
    )
    conn.commit()
    tid = cur.lastrowid
    conn.close()
    return tid


def update_task_status(uuid: str, status: str):
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE tasks SET status = ?, updated_at = ? WHERE uuid = ?", (status, datetime.now(timezone.utc).isoformat(), uuid))
    conn.commit()
    conn.close()


def get_task(uuid: str):
    conn = _get_conn()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM tasks WHERE uuid = ?", (uuid,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def add_tool_call(task_uuid: str, tool: str, input_text: Any, output_text: Any = "") -> None:
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO tool_calls (task_id, tool, input, output, created_at) VALUES ((SELECT id FROM tasks WHERE uuid = ?), ?, ?, ?, ?)",
        (task_uuid, tool, input_text, output_text, datetime.now(timezone.utc).isoformat()),
    )
    conn.commit()
    conn.close()


def add_task_event(task_uuid: str, event_type: str, payload: Any) -> None:
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO task_events (task_id, event_type, payload, created_at) VALUES ((SELECT id FROM tasks WHERE uuid = ?), ?, ?, ?)",
        (task_uuid, event_type, json.dumps(payload), datetime.now(timezone.utc).isoformat()),
    )
    conn.commit()
    conn.close()

