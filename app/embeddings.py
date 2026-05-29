import hashlib
import math
from typing import List

class EmbeddingsProvider:
    """Simple deterministic embedding provider for offline testing.

    Produces fixed-size vectors derived from SHA256 hash of input text.
    """

    def __init__(self, dim: int = 128):
        self.dim = dim

    def embed(self, texts: List[str]) -> List[List[float]]:
        vectors = []
        for t in texts:
            h = hashlib.sha256(t.encode("utf-8")).digest()
            # expand hash to floats
            vec: List[float] = []
            i = 0
            while len(vec) < self.dim:
                b = h[i % len(h)]
                vec.append((b / 255.0) * 2 - 1)
                i += 1
            # normalize
            norm = math.sqrt(sum(x * x for x in vec)) or 1.0
            vec = [x / norm for x in vec]
            vectors.append(vec)
        return vectors
