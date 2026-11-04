from __future__ import annotations

import json


def render_markdown(result: dict) -> str:
    lines = ["# PR Review Report", "", f"Findings: {result['finding_count']}", ""]
    if not result["findings"]:
        lines.append("No findings. Human approval is still required before merge.")
        return "\n".join(lines)
    for f in result["findings"]:
        lines.append(f"## {f['severity'].upper()}: {f['title']}")
        lines.append(f"- File: `{f['file']}:{f['line']}`")
        lines.append(f"- Evidence: `{f['evidence']}`")
        lines.append(f"- Suggestion: {f['suggestion']}")
        lines.append("")
    lines.append("> Human approval required before merge. This report is not an approval.")
    return "\n".join(lines)


def render_json(result: dict) -> str:
    return json.dumps(result, indent=2, ensure_ascii=False)
