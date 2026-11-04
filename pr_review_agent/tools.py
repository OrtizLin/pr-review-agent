from __future__ import annotations

import re
import subprocess
from pathlib import Path

from .config import Config
from .retrieval import retrieve_top


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
    """RAG: TF-IDF retrieval over docs/guidelines.md.

    Returns the top 3 guideline lines for the diff. If nothing scores
    above zero, fall back to the full short file rather than silently
    dropping a rule. See eval/compare_retrieval.py for the comparison
    against the old keyword/full-file method.
    """
    guidelines_file = config.guidelines_dir / "guidelines.md"
    if not guidelines_file.exists():
        return "No team guidelines found."
    text = guidelines_file.read_text()
    lines = [line.strip() for line in text.splitlines() if line.strip().startswith("-")]
    if not lines:
        return text
    top = retrieve_top(lines, diff_text, top_k=3)
    if not top or top[0][1] <= 0:
        return text
    return "\n".join(f"- {line} (score {score})" for line, score in top)
