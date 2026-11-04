"""Generate eval/cases.json (24 cases).

Run: python eval/generate_cases.py
The dry-run reviewer is rule-based, so cases are written against the
rules in pr_review_agent/agent.py, not against a model's opinions.
A case passes only when every expected title is found and no finding
points at a forbidden file.
"""
import json
from pathlib import Path


def diff(path, added):
    lines = [
        f"diff --git a/{path} b/{path}",
        f"--- a/{path}",
        f"+++ b/{path}",
        "@@ -1 +1 @@",
    ]
    for line in added:
        lines.append(f"+{line}")
    return "\n".join(lines) + "\n"


def case(id, path, added, expected, severities=None):
    c = {
        "id": id,
        "diff": diff(path, added),
        "expected_titles": expected,
        "forbidden_files": ["nope.py"],
    }
    if severities:
        c["expected_severities"] = severities
    return c


CASES = [
    case("bare-except-basic", "a.py", ["try:", "    do()", "except:", "    pass"],
         ["Bare except hides real errors"]),
    case("bare-except-nested", "a.py", ["def f():", "    try:", "        x()", "    except:", "        return None"],
         ["Bare except hides real errors"]),
    case("bare-except-with-log", "a.py", ["try:", "    x()", "except:", "    log('err')"],
         ["Bare except hides real errors"]),
    case("print-debug", "a.py", ["def f():", "    print(x)"],
         ["Leftover print statement"]),
    case("print-in-loop", "a.py", ["for i in xs:", "    print(i)"],
         ["Leftover print statement"]),
    case("print-error-path", "a.py", ["try:", "    x()", "except ValueError:", "    print('failed')"],
         ["Leftover print statement"]),
    case("todo-feature", "a.py", ["# TODO: add caching"],
         ["Unresolved TODO in new code"]),
    case("todo-refactor", "a.py", ["# TODO: refactor this helper"],
         ["Unresolved TODO in new code"]),
    case("todo-issue", "a.py", ["# TODO: handle retries properly"],
         ["Unresolved TODO in new code"]),
    case("password-hardcoded", "a.py", ['password = "hunter2"'],
         ["Possible hardcoded secret"]),
    case("password-empty", "a.py", ['password = ""'],
         ["Possible hardcoded secret"]),
    case("password-with-comment", "a.py", ['password = "x"  # temp'],
         ["Possible hardcoded secret"]),
    case("combined-bare-print-todo", "a.py",
         ["try:", "    x()", "except:", "    print('err')", "# TODO: fix"],
         ["Bare except hides real errors", "Leftover print statement", "Unresolved TODO in new code"]),
    case("combined-password-bare", "a.py",
         ["try:", "    x()", "except:", "    pass", 'password = "x"'],
         ["Bare except hides real errors", "Possible hardcoded secret"]),
    case("clean-logging", "a.py",
         ["import logging", "try:", "    x()", "except ValueError:", "    logging.warning('bad input')"],
         []),
    case("clean-specific-except", "a.py",
         ["try:", "    x()", "except KeyError:", "    return None"],
         []),
    case("clean-function", "a.py",
         ["def add(a, b):", "    return a + b"],
         []),
    case("clean-docstring", "a.py",
         ['"""Return the total."""', "def total(xs):", "    return sum(xs)"],
         []),
    case("multi-file-bare-and-print", "a.py",
         ["try:", "    x()", "except:", "    pass"], []),  # placeholder, replaced below
    case("multi-file-password-and-todo", "b.py",
         ['password = "x"'], ["Possible hardcoded secret"]),
    case("severity-password-blocker", "a.py", ['password = "x"'],
         ["Possible hardcoded secret"], {"Possible hardcoded secret": "blocker"}),
    case("severity-bare-major", "a.py", ["try:", "    x()", "except:", "    pass"],
         ["Bare except hides real errors"], {"Bare except hides real errors": "major"}),
    case("severity-print-minor", "a.py", ["print(x)"],
         ["Leftover print statement"], {"Leftover print statement": "minor"}),
    case("clean-diff", "a.py", ["x = 2"], []),
]

# Fix the multi-file case: it needs two files in one diff.
CASES[18] = {
    "id": "multi-file-bare-and-print",
    "diff": (
        "diff --git a/a.py b/a.py\n--- a/a.py\n+++ b/a.py\n@@ -1 +1 @@\n+try:\n+    x()\n+except:\n+    pass\n"
        "diff --git a/b.py b/b.py\n--- a/b.py\n+++ b/b.py\n@@ -1 +1 @@\n+print(x)\n"
    ),
    "expected_titles": ["Bare except hides real errors", "Leftover print statement"],
    "forbidden_files": ["nope.py"],
}

if __name__ == "__main__":
    out = Path(__file__).parent / "cases.json"
    out.write_text(json.dumps(CASES, indent=2) + "\n")
    print(f"Wrote {len(CASES)} cases to {out}")
