# Architecture

```
CLI (human boundary)
  -> git_tools.parse_unified_diff / git_diff
  -> tools: lint, tests, search, retrieve_guidelines (RAG)
  -> agent loop: draft -> validate -> report
  -> report.md + report.json (human reviews, then decides)
```

Design choices, and why:

- Tools run before any LLM draft. The model never has to guess what
  the linter or tests said.
- Validation is separate from drafting. If a draft cites a file or line
  outside the diff, it is dropped. This is what makes the output safe
  to show to a human reviewer.
- The LLM is one function (`review_with_llm`). Swapping providers does
  not change the schema, the validation, or the CLI contract.
- No merge, push, or repo write happens in this tool. That boundary is
  deliberate: the agent advises, the human approves.

Planned next steps:

1. Replace keyword guideline retrieval with embeddings; compare on
   `eval/cases.json` before switching.
2. Add a real LLM provider behind env vars, with prompt versioning.
3. Add a GitHub Action that posts the Markdown report as a PR comment
   (still no auto-merge).
