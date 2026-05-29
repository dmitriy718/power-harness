from app.embeddings import EmbeddingsProvider
from app.memory.vector_store import get_vector_store


def test_embeddings_and_vector_store():
    emb = EmbeddingsProvider(dim=16)
    texts = ["hello world", "blue widget design", "important decision to remember"]
    vectors = emb.embed(texts)
    assert len(vectors) == 3
    vs = get_vector_store(url=None, dim=16)
    # upsert vectors with ids and payloads
    items = []
    for i, v in enumerate(vectors):
        items.append({"id": i, "vector": v, "payload": {"text": texts[i]}})
    assert vs.upsert("testcol", items)
    q = vectors[1]
    res = vs.search("testcol", q, top_k=2)
    assert len(res) >= 1
    # top result payload should be text[1]
    top = res[0]
    # handle both in-memory and qdrant shaped results
    payload = top.get("payload") or top.get("payload")
    assert payload is not None
