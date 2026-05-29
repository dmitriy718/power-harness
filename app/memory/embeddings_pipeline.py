from typing import List, Optional
from ..llm import make_embeddings
from .vector_store import get_vector_store
from ..observability.logging import get_logger

logger = get_logger("memory.embeddings")


def index_texts(collection: str, texts: List[str], ids: Optional[List[str]] = None, project_id: Optional[int] = None):
    emb = make_embeddings()
    vectors = emb.embed_documents(texts)
    store = get_vector_store()
    points = []
    for i, vec in enumerate(vectors):
        pid = ids[i] if ids and i < len(ids) else None
        payload = {"text": texts[i], "project_id": project_id}
        points.append({"id": pid or i, "vector": vec, "payload": payload})
    ok = store.upsert(collection, points)
    logger.info("Indexed %s vectors into %s", len(points), collection)
    return ok


def query_similar(collection: str, query: str, top_k: int = 5):
    emb = make_embeddings()
    qvec = emb.embed_query(query)
    store = get_vector_store()
    res = store.search(collection, qvec, top_k=top_k)
    return res
