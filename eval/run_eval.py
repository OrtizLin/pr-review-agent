"""Score the dry-run reviewer on eval/cases.json.

Pass = every expected title found, every expected severity matches,
and no finding points at a forbidden file. Expand cases with
eval/generate_cases.py; do not report a tuned prompt on the same
cases as if they were held out.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from pr_review_agent.agent import draft_findings, validate_findings
from pr_review_agent.git_tools import parse_unified_diff


def main() -> int:
    base = Path(__file__).parent
    cases = json.loads((base / "cases.json").read_text())
    passed = 0
    for case in cases:
        if "diff_file" in case:
            text = (base / case["diff_file"]).read_text()
        else:
            text = case["diff"]
        diff = parse_unified_diff(text)
        findings = validate_findings(diff, draft_findings(diff))
        titles = [f.title for f in findings]
        by_title = {f.title: f.severity for f in findings}
        ok = all(t in titles for t in case["expected_titles"])
        ok = ok and not any(f.file in case["forbidden_files"] for f in findings)
        for title, severity in case.get("expected_severities", {}).items():
            ok = ok and by_title.get(title) == severity
        print(f"{case['id']}: {'PASS' if ok else 'FAIL'} (found: {titles})")
        passed += int(ok)
    print(f"{passed}/{len(cases)} cases passed")
    return 0 if passed == len(cases) else 1


if __name__ == "__main__":
    raise SystemExit(main())
