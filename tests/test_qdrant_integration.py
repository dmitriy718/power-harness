import os
import pytest

from app.memory.vector_store import get_vector_store, QDRANT_AVAILABLE


@pytest.mark.skipif(not QDRANT_AVAILABLE, reason="qdrant-client not installed")
def test_qdrant_upsert_and_search():
    url = os.environ.get("QDRANT_URL", "http://localhost:6333")
    # Only run when QDRANT_URL is explicitly set or local qdrant is running
    if not os.environ.get("QDRANT_URL"):
        # quick health check
        import requests
        try:
            r = requests.get(f"{url}/api/v1/collections")
            if r.status_code != 200:
                pytest.skip("Qdrant not reachable on default URL")
        except requests.RequestException:
            pytest.skip("Qdrant not reachable on default URL")

    store = get_vector_store(url=url, dim=4)
    # create a small collection and upsert vectors
    col = "test_collection"
    vectors = [
        {"id": 1, "vector": [1.0, 0.0, 0.0, 0.0], "payload": {"text": "one"}},
        {"id": 2, "vector": [0.0, 1.0, 0.0, 0.0], "payload": {"text": "two"}},
    ]
    ok = store.upsert(col, vectors)
    assert ok == True

    res = store.search(col, [1.0, 0.0, 0.0, 0.0], top_k=1)
    assert len(res) >= 1
    assert res[0]["id"] in (1, 2) or res[0].get("id") == 1
