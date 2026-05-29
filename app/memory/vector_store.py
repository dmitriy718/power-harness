from typing import Any, Dict, List, Optional
import os

from ..observability.logging import get_logger

try:
    from qdrant_client import QdrantClient
    from qdrant_client.http import models as rest
    QDRANT_AVAILABLE = True
except Exception:
    QDRANT_AVAILABLE = False

logger = get_logger("memory.vector_store")

_vector_store: Optional[Any] = None

class InMemoryVectorStore:
    def __init__(self, dim: int = 128):
        self.dim = dim
        self.collections: Dict[str, List[Dict[str, Any]]] = {}

    def upsert(self, collection: str, vectors: List[Dict[str, Any]]):
        col = self.collections.setdefault(collection, [])
        col.extend(vectors)
        return True

    def search(self, collection: str, query_vector, top_k: int = 10):
        col = self.collections.get(collection, [])
        # cosine similarity
        def score(v):
            vec = v.get("vector")
            dot = sum(a * b for a, b in zip(vec, query_vector))
            return dot
        scored = sorted(col, key=score, reverse=True)
        return scored[:top_k]


class QdrantVectorStore:
    def __init__(self, url: Optional[str] = None, dim: int = 128):
        from typing import Any as _Any

        self.url = url or os.environ.get("QDRANT_URL")
        self.dim = dim
        if not QDRANT_AVAILABLE:
            raise RuntimeError("qdrant-client not available")
        self.client: _Any = QdrantClient(url=self.url)

    def _ensure_collection(self, collection: str) -> None:
        try:
            if not self.client.collection_exists(collection_name=collection):
                logger.info("Creating Qdrant collection %s with dim=%s", collection, self.dim)
                self.client.create_collection(
                    collection_name=collection,
                    vectors_config=rest.VectorParams(size=self.dim, distance=rest.Distance.COSINE),
                )
        except Exception as exc:
            logger.warning("Qdrant collection validation failed for %s: %s", collection, exc)
            raise

    def upsert(self, collection: str, vectors: List[Dict[str, Any]]):
        self._ensure_collection(collection)
        points = []
        for i, v in enumerate(vectors):
            vid = v.get("id")
            if vid is None:
                vid = i
            vec = v.get("vector") or []
            payload = v.get("payload") or {}
            points.append(rest.PointStruct(id=vid, vector=list(vec), payload=payload))
        try:
            self.client.upload_collection(collection_name=collection, points=points, wait=True)
            return True
        except Exception:
            logger.exception("Qdrant upsert failed for %s", collection)
            logger.debug("Failed vectors=%s", vectors)
            return False

    def search(self, collection: str, query_vector, top_k: int = 10):
        try:
            self._ensure_collection(collection)
            response = self.client.query_points(
                collection_name=collection,
                query=list(query_vector),
                limit=top_k,
                with_payload=True,
            )
            results = []
            for point in getattr(response, "points", []):
                results.append(
                    {
                        "id": getattr(point, "id", None),
                        "score": getattr(point, "score", None),
                        "payload": getattr(point, "payload", None),
                        "vector": getattr(point, "vector", None),
                    }
                )
            return results
        except Exception as exc:
            logger.warning("Qdrant search failed for %s: %s", collection, exc)
            return []


# Factory

def get_vector_store(url: Optional[str] = None, dim: int = 128):
    global _vector_store
    if _vector_store is not None:
        return _vector_store

    qdrant_url = url or os.environ.get("QDRANT_URL")
    if qdrant_url and QDRANT_AVAILABLE:
        try:
            _vector_store = QdrantVectorStore(url=qdrant_url, dim=dim)
            logger.info("Using Qdrant vector store at %s", qdrant_url)
            return _vector_store
        except Exception as exc:
            logger.warning("Qdrant unavailable, falling back to in-memory vector store: %s", exc)
    elif qdrant_url and not QDRANT_AVAILABLE:
        logger.warning("Qdrant URL configured but qdrant-client is not installed; using in-memory vector store")
    else:
        logger.info("No Qdrant configuration found; using in-memory vector store")

    _vector_store = InMemoryVectorStore(dim=dim)
    return _vector_store
