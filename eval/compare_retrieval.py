"""Compare keyword/full-file retrieval vs TF-IDF vs embedding retrieval.

Two query sets, both written against docs/guidelines.md:
  - QUERIES: the original keyword queries (4). TF-IDF already scores 4/4 here.
  - PARAPHRASE_QUERIES: same meanings, deliberately avoiding the
    guideline's own keywords (except, password, print, TODO). These
    were written from the guideline meanings BEFORE any embedding
    scores for them were seen, so they are not tuned to the embedding
    model.

The old keyword method returned the whole file whenever any keyword
matched (precision 1/5 on a 5-line file, even when it 'found' the
right line). TF-IDF and embedding both return top 3 by cosine
similarity, scored by the same top-1 rule.

Win rule, stated in advance: embedding becomes the default only if
it beats TF-IDF on the paraphrase set AND does not lose on the
original set. A tie on both sets keeps TF-IDF as the default.
If no embedding key is set, the embedding run is reported as
skipped, not faked.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from pr_review_agent.retrieval import retrieve_top, retrieve_top_embedding

QUERIES = [
    ("bare except handling", "Do not use a bare `except:`; catch a specific exception and log it."),
    ("hardcoded password secret", "Do not hardcode secrets such as `password =`; use env / secret manager."),
    ("print logging production", "Do not leave `print(` in production code; use logging."),
    ("TODO tracked issue", "Do not leave an unresolved `TODO` in new code without a tracked issue."),
]

PARAPHRASE_QUERIES = [
    ("catching every error without naming the type and without recording it",
     "Do not use a bare `except:`; catch a specific exception and log it."),
    ("storing a credential directly in source code instead of a vault",
     "Do not hardcode secrets such as `password =`; use env / secret manager."),
    ("leaving debug output in shipped code instead of proper logging",
     "Do not leave `print(` in production code; use logging."),
    ("marking unfinished work in code with no ticket to track it",
     "Do not leave an unresolved `TODO` in new code without a tracked issue."),
    ("a review comment with no evidence from the change, a tool, or a rule",
     "Every finding in a review must cite a diff line, a tool result, or a guideline."),
]


def _is_top1(top, expected):
    return bool(top) and top[0][0].lstrip("- ").strip() == expected


def _run_set(label, queries, lines, retriever_fn):
    correct = 0
    rows = []
    for query, expected in queries:
        top = retriever_fn(lines, query)
        ok = _is_top1(top, expected)
        correct += int(ok)
        rows.append((query, expected, top, ok))
        print(f"[{label}] Query: {query}")
        print(f"  Top 3: {top}")
        print(f"  Top-1 correct: {ok}")
    print(f"[{label}] {correct}/{len(queries)}")
    return correct, rows


def main() -> int:
    base = Path(__file__).parent.parent
    lines = [
        line.strip()
        for line in (base / "docs" / "guidelines.md").read_text().splitlines()
        if line.strip().startswith("-")
    ]
    print(f"Guideline lines: {len(lines)}")
    print(f"Old keyword method: whole file every time, precision 1/{len(lines)} by construction.\n")

    tfidf_orig, orig_rows = _run_set(
        "TF-IDF original", QUERIES, lines,
        lambda docs, q: retrieve_top(docs, q, top_k=3))
    print()
    tfidf_para, para_rows = _run_set(
        "TF-IDF paraphrase", PARAPHRASE_QUERIES, lines,
        lambda docs, q: retrieve_top(docs, q, top_k=3))
    print()

    emb_orig = emb_para = None
    if os.environ.get("EMBEDDING_API_KEY") or os.environ.get("LLM_API_KEY"):
        from pr_review_agent.embeddings import embed_texts, embedding_config

        cfg = embedding_config()
        print(f"Embedding run: model={cfg['model']} base={cfg['base_url']}\n")
        emb_orig, _ = _run_set(
            "Embedding original", QUERIES, lines,
            lambda docs, q: retrieve_top_embedding(docs, q, embed_texts, top_k=3))
        print()
        emb_para, _ = _run_set(
            "Embedding paraphrase", PARAPHRASE_QUERIES, lines,
            lambda docs, q: retrieve_top_embedding(docs, q, embed_texts, top_k=3))
        print()
        if emb_para > tfidf_para and emb_orig >= tfidf_orig:
            verdict = "Verdict: embedding BEATS TF-IDF on paraphrases without losing on originals -> switch default to embedding."
        else:
            verdict = "Verdict: embedding does NOT beat TF-IDF under the pre-stated rule -> TF-IDF stays the default."
        print(verdict)
    else:
        verdict = "Embedding run: skipped (no EMBEDDING_API_KEY or LLM_API_KEY set)."
        print(verdict)

    md = ["# Retrieval comparison", "",
          f"Guideline lines: {len(lines)}",
          f"TF-IDF original top-1: {tfidf_orig}/{len(QUERIES)}",
          f"TF-IDF paraphrase top-1: {tfidf_para}/{len(PARAPHRASE_QUERIES)}",
          f"Old keyword method: returned the whole file every time, "
          f"so top-1 precision was 1/{len(lines)} by construction.", ""]
    for query, expected, top, ok in orig_rows:
        md.append(f"- Original query `{query}`: TF-IDF top-1 correct = {ok}; top 3 = {top}")
    for query, expected, top, ok in para_rows:
        md.append(f"- Paraphrase query `{query}`: TF-IDF top-1 correct = {ok}; top 3 = {top}")
    md.append("")
    if emb_orig is None:
        md.append("Embedding run: skipped (no key set).")
    else:
        md.append(f"Embedding original top-1: {emb_orig}/{len(QUERIES)}")
        md.append(f"Embedding paraphrase top-1: {emb_para}/{len(PARAPHRASE_QUERIES)}")
        md.append(verdict)
    (Path(__file__).parent / "retrieval_comparison.md").write_text("\n".join(md) + "\n")
    print(f"\nSummary: TF-IDF {tfidf_orig}/{len(QUERIES)} original, {tfidf_para}/{len(PARAPHRASE_QUERIES)} paraphrase"
          + (f"; Embedding {emb_orig}/{len(QUERIES)} original, {emb_para}/{len(PARAPHRASE_QUERIES)} paraphrase" if emb_orig is not None else "; Embedding skipped"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
