from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_embeddings_index_and_query_workflow():
    index_response = client.post(
        "/embeddings/index",
        json={
            "collection": "workflow_test",
            "texts": ["remember this fact", "another detail to store", "important info here"],
            "ids": ["fact1", "fact2", "fact3"],
            "project_id": 1,
        },
    )
    assert index_response.status_code == 200
    assert index_response.json().get("ok") == True

    query_response = client.post(
        "/embeddings/query",
        json={
            "collection": "workflow_test",
            "query": "remember fact",
            "top_k": 2,
        },
    )
    assert query_response.status_code == 200
    results = query_response.json().get("results")
    assert isinstance(results, list)
    assert len(results) >= 1
    assert any(r.get("payload", {}).get("text") for r in results)
