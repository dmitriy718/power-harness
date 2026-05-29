from typing import Optional

from ..memory.sqlite_store import SQLiteMemoryStore
from ..memory.extractor import MemoryExtractor

_extractor = MemoryExtractor()


def get_memory_store(db_path: Optional[str] = None) -> SQLiteMemoryStore:
    return SQLiteMemoryStore(db_path=db_path)


def save_memory(project_id: int, kind: str, content: str, source: str = "agent"):
    score = _extractor.score(content)
    store = get_memory_store()
    return store.save_memory(project_id, kind, content, score=score, source=source)


def search_memory(q: str, limit: int = 10):
    store = get_memory_store()
    return store.search(q, limit=limit)


def list_memory(project_id: Optional[int] = None):
    store = get_memory_store()
    return store.list(project_id)

