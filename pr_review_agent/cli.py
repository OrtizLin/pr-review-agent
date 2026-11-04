from __future__ import annotations

import argparse
from pathlib import Path

from .agent import run_agent
from .config import Config
from .git_tools import git_diff, parse_unified_diff
from .report import render_json, render_markdown


def main() -> None:
    parser = argparse.ArgumentParser(description="PR Review Agent (human approval required)")
    parser.add_argument("--repo", default=".", help="Repo root")
    parser.add_argument("--base", default="main", help="Base ref for git diff")
    parser.add_argument("--head", default="HEAD", help="Head ref for git diff")
    parser.add_argument("--sample", action="store_true", help="Review examples/sample_diff.diff")
    parser.add_argument("--dry-run", action="store_true", default=True, help="Offline rule-based review")
    parser.add_argument("--no-dry-run", dest="dry_run", action="store_false", help="Use the LLM path")
    parser.add_argument("--out-md", default="report.md")
    parser.add_argument("--out-json", default="report.json")
    args = parser.parse_args()

    config = Config(repo_root=Path(args.repo), dry_run=args.dry_run)
    if args.sample:
        sample = Path(__file__).resolve().parent.parent / "examples" / "sample_diff.diff"
        diff = parse_unified_diff(sample.read_text())
    else:
        diff = git_diff(args.repo, args.base, args.head)

    try:
        result = run_agent(diff, config)
    except RuntimeError as exc:
        print(f"Error: {exc}")
        raise SystemExit(1)
    Path(args.out_md).write_text(render_markdown(result))
    Path(args.out_json).write_text(render_json(result))
    print(render_markdown(result))
    print(f"\nWrote {args.out_md} and {args.out_json}. Human approval required before merge.")


if __name__ == "__main__":
    main()
