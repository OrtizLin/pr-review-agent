import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pr_review_agent.embeddings import parse_embeddings_response
from pr_review_agent.retrieval import EmbeddingRetriever


def _stub_embed(texts):
    """Deterministic stub: 3-d vectors from token presence, not a model.

    Used only to test the retriever plumbing (cosine ranking, reuse
    of document vectors, top-k shape). It proves nothing about a real
    embedding model's quality; that is what eval/compare_retrieval.py
    measures with a real key.
    """
    def vec(text):
        low = text.lower()
        return [
            1.0 if "except" in low else 0.0,
            1.0 if "password" in low or "secret" in low else 0.0,
            1.0 if "print" in low else 0.0,
        ]

    return [vec(t) for t in texts]


def test_embedding_retriever_ranks_by_cosine():
    docs = [
        "Do not use a bare except; catch a specific exception and log it.",
        "Do not hardcode secrets such as password =; use env / secret manager.",
        "Do not leave print( in production code; use logging.",
    ]
    retriever = EmbeddingRetriever(docs, _stub_embed)
    top = retriever.retrieve_top("hardcoded password secret", top_k=1)
    assert top and "password" in top[0][0]
    assert 0.0 <= top[0][1] <= 1.0


def test_parse_embeddings_response_orders_by_index():
    body = {
        "data": [
            {"index": 1, "embedding": [0.0, 1.0]},
            {"index": 0, "embedding": [1.0, 0.0]},
        ]
    }
    vectors = parse_embeddings_response(body)
    assert vectors == [[1.0, 0.0], [0.0, 1.0]]


def test_parse_embeddings_response_rejects_empty_vector():
    try:
        parse_embeddings_response({"data": [{"index": 0, "embedding": []}]})
    except ValueError:
        return
    raise AssertionError("empty embedding vector should raise")
