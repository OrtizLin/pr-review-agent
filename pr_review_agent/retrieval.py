"""Local TF-IDF retrieval over guideline lines.

No external dependencies and no network. This is the embedding-style
retriever interface: documents are embedded as TF-IDF vectors, a query
is embedded the same way, and ranking is cosine similarity.

Swap the vectoriser for a model embedding later without changing the
caller: `retrieve_top(documents, query, top_k)` stays the same, and
`eval/compare_retrieval.py` is the comparison to beat.
"""
from __future__ import annotations

import math
import re

_TOKEN = re.compile(r"[a-z0-9_]+")


def tokenize(text: str) -> list[str]:
    return _TOKEN.findall(text.lower())


class TfidfRetriever:
    def __init__(self, documents: list[str]):
        self.documents = documents
        self._doc_freq: dict[str, int] = {}
        for doc in documents:
            for token in set(tokenize(doc)):
                self._doc_freq[token] = self._doc_freq.get(token, 0) + 1
        n = max(len(documents), 1)
        self._idf = {
            token: math.log((n + 1) / (freq + 1)) + 1
            for token, freq in self._doc_freq.items()
        }
        self._vectors = [self._vector(doc) for doc in documents]

    def _vector(self, text: str) -> dict[str, float]:
        counts: dict[str, int] = {}
        for token in tokenize(text):
            counts[token] = counts.get(token, 0) + 1
        vec = {t: c * self._idf.get(t, 1.0) for t, c in counts.items()}
        norm = math.sqrt(sum(v * v for v in vec.values())) or 1.0
        return {t: v / norm for t, v in vec.items()}

    def retrieve_top(self, query: str, top_k: int = 3) -> list[tuple[str, float]]:
        qvec = self._vector(query)
        scored = []
        for doc, vec in zip(self.documents, self._vectors):
            score = sum(qvec.get(t, 0.0) * vec.get(t, 0.0) for t in qvec)
            scored.append((doc, round(score, 4)))
        scored.sort(key=lambda pair: pair[1], reverse=True)
        return scored[:top_k]


def retrieve_top(documents: list[str], query: str, top_k: int = 3) -> list[tuple[str, float]]:
    return TfidfRetriever(documents).retrieve_top(query, top_k=top_k)


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a)) or 1.0
    norm_b = math.sqrt(sum(y * y for y in b)) or 1.0
    return dot / (norm_a * norm_b)


class EmbeddingRetriever:
    """Model-embedding retriever with the same output shape as TF-IDF.

    Takes an embed function (texts -> vectors) so tests can pass a
    stub and production can pass embeddings.embed_texts. Documents
    are embedded once per instance; the query is embedded per call.
    No fallback to TF-IDF happens inside this class: if embedding
    fails, the caller sees the error instead of a silently different
    retriever.
    """

    def __init__(self, documents: list[str], embed):
        self.documents = documents
        self._embed = embed
        self._doc_vectors = embed(documents) if documents else []

    def retrieve_top(self, query: str, top_k: int = 3) -> list[tuple[str, float]]:
        if not self.documents:
            return []
        # Embed only the query here; document vectors are reused
        # from __init__, not re-embedded on every call.
        query_vector = self._embed([query])[0]
        scored = [
            (doc, round(_cosine(query_vector, vec), 4))
            for doc, vec in zip(self.documents, self._doc_vectors)
        ]
        scored.sort(key=lambda pair: pair[1], reverse=True)
        return scored[:top_k]


def retrieve_top_embedding(documents: list[str], query: str, embed, top_k: int = 3) -> list[tuple[str, float]]:
    return EmbeddingRetriever(documents, embed).retrieve_top(query, top_k=top_k)
