"""OpenAI-compatible embeddings client, standard library only.

Env-only configuration, same contract as the LLM boundary in llm.py:
  EMBEDDING_API_KEY  (preferred; falls back to LLM_API_KEY if unset,
                      because a Gemini AI Studio key works for both
                      chat and embeddings on the Gemini endpoint)
  EMBEDDING_BASE_URL (default https://api.openai.com/v1)
  EMBEDDING_MODEL    (default text-embedding-3-small)

Presets (set the base URL and model together, never the key in chat
or in a committed file):
  OpenAI: base https://api.openai.com/v1, model text-embedding-3-small
  Gemini: base https://generativelanguage.googleapis.com/v1beta/openai,
          model gemini-embedding-001
  (Gemini's OpenAI-compatible endpoint supports POST /embeddings.
  Do NOT use text-embedding-004 on this path: it returns HTTP 404
  for many keys on v1beta, even though older docs still list it.
  gemini-embedding-001 outputs 3072 dimensions by default; that is
  fine here because query and documents are embedded with the same
  model in one run and compared by cosine similarity, and no vectors
  are stored in a fixed-dimension database.)

The client never fakes a vector: no key raises a clear error, and a
non-200 response raises with the HTTP status, not a silent fallback.
"""
from __future__ import annotations

import json
import os
import urllib.request


def embedding_config() -> dict[str, str]:
    api_key = os.environ.get("EMBEDDING_API_KEY", "").strip() or os.environ.get("LLM_API_KEY", "").strip()
    return {
        "api_key": api_key,
        "base_url": os.environ.get("EMBEDDING_BASE_URL", "https://api.openai.com/v1").rstrip("/"),
        "model": os.environ.get("EMBEDDING_MODEL", "text-embedding-3-small"),
    }


def parse_embeddings_response(body: dict) -> list[list[float]]:
    data = body.get("data", [])
    ordered = sorted(data, key=lambda item: item.get("index", 0))
    vectors: list[list[float]] = []
    for item in ordered:
        embedding = item.get("embedding")
        if not isinstance(embedding, list) or not embedding:
            raise ValueError("Embeddings response item has no embedding vector.")
        vectors.append([float(v) for v in embedding])
    return vectors


def embed_texts(texts: list[str], timeout: int = 60) -> list[list[float]]:
    config = embedding_config()
    if not config["api_key"]:
        raise RuntimeError(
            "No embedding key set. Set EMBEDDING_API_KEY (or LLM_API_KEY) "
            "in your shell environment, never in chat or a committed file."
        )
    if not texts:
        return []
    payload = json.dumps({"model": config["model"], "input": texts}).encode()
    request = urllib.request.Request(
        f"{config['base_url']}/embeddings",
        data=payload,
        headers={"Authorization": f"Bearer {config['api_key']}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = json.loads(response.read().decode())
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"Embeddings request failed with HTTP {exc.code}. Check model, base URL, and key.") from exc
    return parse_embeddings_response(body)
