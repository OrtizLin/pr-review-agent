# PR Review Report

Findings: 4

## MAJOR: Bare except hides real errors
- File: `examples/sample_repo/app.py:4`
- Evidence: `except:`
- Suggestion: Catch a specific exception and log it.

## MINOR: Leftover print statement
- File: `examples/sample_repo/app.py:5`
- Evidence: `print("failed")`
- Suggestion: Use logging instead of print.

## BLOCKER: Possible hardcoded secret
- File: `examples/sample_repo/app.py:6`
- Evidence: `password = "hunter2"`
- Suggestion: Move the secret to env / secret manager and rotate it.

## MINOR: Unresolved TODO in new code
- File: `examples/sample_repo/app.py:8`
- Evidence: `# TODO: handle retries properly`
- Suggestion: Resolve it or file a tracked issue and reference it.

> Human approval required before merge. This report is not an approval.