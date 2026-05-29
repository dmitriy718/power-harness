import sqlite3
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from pathlib import Path
import os

DB_PATH = Path(os.environ.get("DATABASE_URL", "sqlite:///./data/nova_agent.db").replace("sqlite://", ""))

class SQLiteMemoryStore:
    def __init__(self, db_path: Optional[str] = None):
        self._path = db_path or str(DB_PATH)
        # ensure parent dir exists
        p = Path(self._path)
        if not p.parent.exists():
            p.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self._path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        # ensure schema exists for this DB
        try:
            from ..storage.db import SCHEMA
            cur = self._conn.cursor()
            cur.executescript(SCHEMA)
            self._conn.commit()
        except Exception as exc:
            pass

    def save_memory(self, project_id: int, kind: str, content: str, score: float = 0.0, source: str = "agent") -> int:
        cur = self._conn.cursor()
        cur.execute(
            "INSERT INTO memories (project_id, kind, content, score, created_at, source, confidence) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (project_id, kind, content, score, datetime.now(timezone.utc).isoformat(), source, 1.0),
        )
        self._conn.commit()
        lid = cur.lastrowid if cur.lastrowid is not None else 0
        return int(lid)

    def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        # naive full-text like search
        cur = self._conn.cursor()
        like = f"%{query}%"
        cur.execute("SELECT * FROM memories WHERE content LIKE ? ORDER BY score DESC LIMIT ?", (like, limit))
        rows = cur.fetchall()
        return [dict(r) for r in rows]

    def list(self, project_id: Optional[int] = None) -> List[Dict[str, Any]]:
        cur = self._conn.cursor()
        if project_id:
            cur.execute("SELECT * FROM memories WHERE project_id = ?", (project_id,))
        else:
            cur.execute("SELECT * FROM memories")
        return [dict(r) for r in cur.fetchall()]

    def delete(self, memory_id: int) -> None:
        cur = self._conn.cursor()
        cur.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
        self._conn.commit()

