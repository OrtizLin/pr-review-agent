"""Score the dry-run reviewer on eval/heldout_cases.json.

HELD-OUT RULES, READ BEFORE EDITING ANYTHING HERE:
- These cases were written after the 24 development cases, with
  different scenarios, and were NOT used to tune rules or prompts.
- Run this file and report the result as-is. Do NOT change code,
  rules, or prompts to make a failing held-out case pass, and do
  NOT merge these cases into eval/cases.json. Fixing code after
  seeing held-out failures turns this set into a development set
  and its score stops meaning anything about generalisation.
- If a held-out case fails, report it as a failure with its id,
  and treat the failure as evidence about the current code, not
  as a task to immediately patch for this score.

Pass = every expected title found, every expected severity
matches, no finding points at a forbidden file, and (for clean
cases) no findings at all.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pr_review_agent.agent import draft_findings, validate_findings
from pr_review_agent.git_tools import parse_unified_diff


def main() -> int:
    base = Path(__file__).resolve().parent
    cases = json.loads((base / "heldout_cases.json").read_text())
    passed = 0
    for case in cases:
        diff = parse_unified_diff(case["diff"])
        findings = validate_findings(diff, draft_findings(diff))
        titles = [f.title for f in findings]
        by_title = {f.title: f.severity for f in findings}
        ok = all(t in titles for t in case["expected_titles"])
        ok = ok and not any(f.file in case["forbidden_files"] for f in findings)
        # Clean cases must have no findings at all, not just the expected ones.
        if not case["expected_titles"]:
            ok = ok and not findings
        for title, severity in case.get("expected_severities", {}).items():
            ok = ok and by_title.get(title) == severity
        print(f"{case['id']}: {'PASS' if ok else 'FAIL'} (found: {titles})")
        passed += int(ok)
    print(f"Held-out: {passed}/{len(cases)} cases passed")
    print("Note: this score is separate from the 24/24 development score in eval/run_eval.py.")
    return 0 if passed == len(cases) else 1


if __name__ == "__main__":
    raise SystemExit(main())
