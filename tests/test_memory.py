from app.memory.sqlite_store import SQLiteMemoryStore


def test_memory_save_and_search(tmp_path):
    db = tmp_path / "test.db"
    store = SQLiteMemoryStore(db_path=str(db))
    mid = store.save_memory(project_id=1, kind="episodic", content="This is an important decision to remember.")
    assert isinstance(mid, int)
    results = store.search("important")
    assert len(results) >= 1

