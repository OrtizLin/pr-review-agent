"""Compare keyword/full-file retrieval vs TF-IDF retrieval.

Queries are written against docs/guidelines.md. The old method returned
the whole file whenever any keyword matched (precision 1/5 on a 5-line
file, even when it 'found' the right line). TF-IDF returns the top 3
lines by cosine similarity. Output is printed and written to
eval/retrieval_comparison.md.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from pr_review_agent.retrieval import retrieve_top

QUERIES = [
    ("bare except handling", "Do not use a bare `except:`; catch a specific exception and log it."),
    ("hardcoded password secret", "Do not hardcode secrets such as `password =`; use env / secret manager."),
    ("print logging production", "Do not leave `print(` in production code; use logging."),
    ("TODO tracked issue", "Do not leave an unresolved `TODO` in new code without a tracked issue."),
]


def main() -> int:
    base = Path(__file__).parent.parent
    lines = [
        line.strip()
        for line in (base / "docs" / "guidelines.md").read_text().splitlines()
        if line.strip().startswith("-")
    ]
    rows = []
    tfidf_top1 = 0
    for query, expected in QUERIES:
        top = retrieve_top(lines, query, top_k=3)
        # Retrieved lines keep their "- " bullet; expected strings do not.
        is_top1 = bool(top) and top[0][0].lstrip("- ").strip() == expected
        tfidf_top1 += int(is_top1)
        rows.append((query, expected, top, is_top1))
        print(f"Query: {query}")
        print(f"  Expected: {expected}")
        print(f"  TF-IDF top 3: {top}")
        print(f"  Top-1 correct: {is_top1}")
        print(f"  Old keyword method: whole file ({len(lines)} lines, precision 1/{len(lines)})")
    md = ["# Retrieval comparison", "",
          f"Guideline lines: {len(lines)}",
          f"TF-IDF top-1 correct: {tfidf_top1}/{len(QUERIES)}",
          f"Old keyword method: returned the whole file every time, "
          f"so top-1 precision was 1/{len(lines)} by construction.", ""]
    for query, expected, top, is_top1 in rows:
        md.append(f"- Query `{query}`: top-1 correct = {is_top1}; top 3 = {top}")
    (Path(__file__).parent / "retrieval_comparison.md").write_text("\n".join(md) + "\n")
    print(f"\nTF-IDF top-1: {tfidf_top1}/{len(QUERIES)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
