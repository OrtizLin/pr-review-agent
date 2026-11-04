from pathlib import Path

from pr_review_agent.llm import parse_llm_response
from pr_review_agent.retrieval import retrieve_top


def test_parse_llm_response_keeps_only_valid_findings():
    text = (
        'Here is the review: [{"file": "a.py", "line": 3, "severity": "major", '
        '"title": "Bare except", "evidence": "except:", "suggestion": "Be specific."}, '
        '{"file": "nope.py", "line": "x", "severity": "major", "title": "Bad"}]'
    )
    findings = parse_llm_response(text)
    assert len(findings) == 1
    assert findings[0]["file"] == "a.py"
    assert findings[0]["line"] == 3


def test_parse_llm_response_rejects_non_json():
    assert parse_llm_response("no json here") == []


def test_retrieval_top1_is_relevant_guideline():
    docs = Path(__file__).parent.parent / "docs" / "guidelines.md"
    lines = [line.strip() for line in docs.read_text().splitlines() if line.strip().startswith("-")]
    top = retrieve_top(lines, "hardcoded password secret", top_k=3)
    assert "password" in top[0][0]
    assert top[0][1] > 0
