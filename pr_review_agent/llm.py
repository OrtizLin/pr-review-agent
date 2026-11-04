"""OpenAI-compatible LLM boundary. No vendor SDK, no committed keys.

Configuration is env-only:
  LLM_API_KEY   (required for the LLM path; never put it in chat or a file)
  LLM_BASE_URL  (default https://api.openai.com/v1)
  LLM_MODEL     (default gpt-4o-mini; set whatever you actually have access to)

The model must return a JSON list of findings. Anything else is parsed
strictly and then re-validated by agent.validate_findings(), so a model
cannot invent files or lines into the final report.
"""
from __future__ import annotations

import json
import os
import urllib.request


def parse_llm_response(text: str) -> list[dict]:
    """Extract the first JSON list from model output and keep only valid items."""
    start = text.find("[")
    end = text.rfind("]")
    if start < 0 or end < start:
        return []
    try:
        data = json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return []
    findings = []
    if not isinstance(data, list):
        return []
    for item in data:
        if not isinstance(item, dict):
            continue
        try:
            line = int(item["line"])
        except (KeyError, TypeError, ValueError):
            continue
        if item.get("severity") not in {"blocker", "major", "minor"}:
            continue
        if not item.get("file") or not item.get("title"):
            continue
        findings.append(
            {
                "file": str(item["file"]),
                "line": line,
                "severity": str(item["severity"]),
                "title": str(item["title"]),
                "evidence": str(item.get("evidence", "")),
                "suggestion": str(item.get("suggestion", "")),
            }
        )
    return findings


def complete_review(system_prompt: str, user_prompt: str, timeout: int = 60) -> list[dict]:
    api_key = os.environ.get("LLM_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError(
            "LLM_API_KEY is not set. Set it in your shell environment "
            "(never in chat, never in a committed file) and retry with --no-dry-run."
        )
    base_url = os.environ.get("LLM_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    model = os.environ.get("LLM_MODEL", "gpt-4o-mini")
    payload = json.dumps(
        {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.2,
        }
    ).encode()
    request = urllib.request.Request(
        f"{base_url}/chat/completions",
        data=payload,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        body = json.loads(response.read().decode())
    content = body["choices"][0]["message"]["content"]
    return parse_llm_response(content)
