# Demo script (about 2 minutes)

Do not read this verbatim on camera; it is the timing plan. Run the
commands, show the report, and stop before any merge.

## 0:00-0:20 The problem
"Pull request reviews are slow and inconsistent. This agent runs tools
first, then drafts a review a human approves. It never merges by itself."

## 0:20-0:50 Run it (dry-run, offline)
```bash
python -m pr_review_agent.cli --sample --dry-run
```
Show the 4 findings on screen: bare except, leftover print, possible
hardcoded secret (blocker), unresolved TODO, each with file and line.

## 0:50-1:20 Why it is not just a chatbot
Point at the code while talking:
- `tools.py`: lint, tests, search, guideline retrieval
- `retrieval.py`: TF-IDF retrieval, compared in `eval/retrieval_comparison.md`
- `agent.py`: validation drops any finding outside the diff
- `eval/`: 24 cases, all passing; `tests/`: pytest, all passing

## 1:20-1:50 The LLM path (honest boundary)
```bash
# LLM_API_KEY must already be in your shell env; never on screen, never committed
python -m pr_review_agent.cli --sample --no-dry-run
```
Say: "Without a key it errors clearly instead of faking a review.
With a key it uses the same validated schema, so the model cannot
invent files or lines into the final report."

## 1:50-2:00 Close
"Next steps I would do in production: model embeddings for retrieval,
a PR-comment action, and a held-out eval set. Human approval stays
required before merge."

## Demo run log
See `docs/demo_run.log` for the exact dry-run output captured during
development. Re-run the sample command before recording so the log
matches your screen.
