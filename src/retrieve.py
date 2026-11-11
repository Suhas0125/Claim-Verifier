"""Three retrieval setups: embeddings only, BM25 only, and hybrid (RRF)."""
import re
import numpy as np
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


class Retriever:
    def __init__(self, chunks: list[dict]):
        self.chunks = chunks
        texts = [c["text"] for c in chunks]
        self.model = SentenceTransformer(MODEL_NAME)
        self.emb = self.model.encode(texts, normalize_embeddings=True)
        self.bm25 = BM25Okapi([tokenize(t) for t in texts])

    def _dense_scores(self, query: str) -> np.ndarray:
        q = self.model.encode([query], normalize_embeddings=True)[0]
        return self.emb @ q

    def _bm25_scores(self, query: str) -> np.ndarray:
        return np.array(self.bm25.get_scores(tokenize(query)))

    def search(self, query: str, k: int = 3, mode: str = "hybrid") -> list[dict]:
        """mode: 'dense', 'bm25', or 'hybrid'. Returns top-k chunks with scores."""
        if mode == "dense":
            scores = self._dense_scores(query)
        elif mode == "bm25":
            scores = self._bm25_scores(query)
        else:  # reciprocal rank fusion
            scores = np.zeros(len(self.chunks))
            for s in (self._dense_scores(query), self._bm25_scores(query)):
                ranks = np.argsort(np.argsort(-s))
                scores += 1.0 / (60 + ranks + 1)
        top = np.argsort(-scores)[:k]
        return [{**self.chunks[i], "score": float(scores[i])} for i in top]


if __name__ == "__main__":
    from src.ingest import load_chunks

    r = Retriever(load_chunks())
    for q in ["Net profit was Rs 130 crore",
              "termination requires 60 days notice",
              "Circular CYB/2024/17 requires disclosure within 24 hours"]:
        print("\nQ:", q)
        for mode in ("dense", "bm25", "hybrid"):
            top = r.search(q, k=1, mode=mode)[0]
            print(f"  {mode:6s} -> {top['text'][:70]}")