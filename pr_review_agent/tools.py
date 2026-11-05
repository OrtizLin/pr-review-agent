from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

from .config import Config
from .retrieval import retrieve_top, retrieve_top_embedding


def run_lint(repo_root: Path) -> str:
    """Tool: linter. Returns a short summary, never a hallucinated run."""
    try:
        result = subprocess.run(
            ["ruff", "check", "."],
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=60,
        )
        output = (result.stdout + result.stderr).strip()
        return output[:2000] if output else "ruff: no findings"
    except FileNotFoundError:
        return "ruff: not installed, lint skipped"
    except subprocess.TimeoutExpired:
        return "ruff: timed out, lint skipped"


def run_tests(repo_root: Path, timeout: int) -> str:
    """Tool: test suite. Skipped cleanly when there is no suite."""
    if not list(repo_root.glob("test_*.py")) and not (repo_root / "tests").exists():
        return "tests: no test suite found, skipped"
    try:
        result = subprocess.run(
            ["python3", "-m", "pytest", "-q"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except FileNotFoundError:
        return "tests: python3 not found, skipped"
    except subprocess.TimeoutExpired:
        return "tests: timed out"
    tail = (result.stdout + result.stderr).strip().splitlines()[-5:]
    return "\n".join(tail) if tail else "tests: no output"


def search_codebase(repo_root: Path, pattern: str) -> list[str]:
    """Tool: plain-text search over changed-file types. No network."""
    hits: list[str] = []
    for path in repo_root.rglob("*.py"):
        if ".venv" in path.parts or "__pycache__" in path.parts:
            continue
        try:
            text = path.read_text(errors="ignore")
        except OSError:
            continue
        for i, line in enumerate(text.splitlines(), 1):
            if re.search(pattern, line):
                hits.append(f"{path.relative_to(repo_root)}:{i}: {line.strip()}")
                if len(hits) >= 20:
                    return hits
    return hits


def retrieve_guidelines(config: Config, diff_text: str) -> str:
    """RAG retrieval over docs/guidelines.md.

    Default retriever, after the 2026-11-05 comparison (TF-IDF 4/4
    original + 2/5 paraphrase; embedding 4/4 original + 5/5
    paraphrase, gemini-embedding-001): embedding when an embedding
    key is set, otherwise TF-IDF. The choice is stated in the
    returned text, so it is never a silent fallback. Set
    RETRIEVER=embedding to force embedding (raises a clear error
    with no key) or RETRIEVER=tfidf to force TF-IDF offline.
    Returns the top 3 guideline lines for the diff. If nothing
    scores above zero, fall back to the full short file rather
    than silently dropping a rule.
    """
    guidelines_file = config.guidelines_dir / "guidelines.md"
    if not guidelines_file.exists():
        return "No team guidelines found."
    text = guidelines_file.read_text()
    lines = [line.strip() for line in text.splitlines() if line.strip().startswith("-")]
    if not lines:
        return text
    requested = os.environ.get("RETRIEVER", "").strip().lower()
    if requested == "embedding":
        retriever_name = "embedding"
    elif requested == "tfidf":
        retriever_name = "tfidf"
    elif os.environ.get("EMBEDDING_API_KEY") or os.environ.get("LLM_API_KEY"):
        retriever_name = "embedding"
    else:
        retriever_name = "tfidf"
    if retriever_name == "embedding":
        from .embeddings import embed_texts

        top = retrieve_top_embedding(lines, diff_text, embed_texts, top_k=3)
    else:
        top = retrieve_top(lines, diff_text, top_k=3)
    if not top or top[0][1] <= 0:
        return text
    header = f"Retriever: {retriever_name}"
    return header + "\n" + "\n".join(f"- {line} (score {score})" for line, score in top)
