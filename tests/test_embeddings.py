from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_embeddings_index_and_query():
    # index a few short texts
    texts = ["alpha", "beta", "gamma"]
    r = client.post("/embeddings/index", json={"collection": "test_coll", "texts": texts, "project_id": 2})
    assert r.status_code == 200
    assert r.json().get("ok") is True

    # query similar
    q = client.post("/embeddings/query", json={"collection": "test_coll", "query": "alpha", "top_k": 2})
    assert q.status_code == 200
    res = q.json()
    assert isinstance(res.get("results"), list)
    assert len(res.get("results")) <= 2
