from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass, field


@dataclass
class ChangedFile:
    path: str
    added_lines: list[tuple[int, str]] = field(default_factory=list)


@dataclass
class Diff:
    files: list[ChangedFile] = field(default_factory=list)

    @property
    def paths(self) -> set[str]:
        return {f.path for f in self.files}

    def text(self) -> str:
        out = []
        for f in self.files:
            for lineno, line in f.added_lines:
                out.append(f"{f.path}:{lineno}: {line}")
        return "\n".join(out)


_DIFF_FILE = re.compile(r"^diff --git a/(.+?) b/(.+?)$")
_NEW_FILE = re.compile(r"^\+\+\+ b/(.+)$")
_HUNK = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@")
_ADDED = re.compile(r"^\+(?!\+\+)(.*)$")


def parse_unified_diff(text: str) -> Diff:
    """Parse a unified diff into added lines only.

    This is deliberately small and testable: the agent only reviews
    added lines, so a finding can never point at unchanged code.
    """
    diff = Diff()
    current: ChangedFile | None = None
    new_lineno = 0
    for raw in text.splitlines():
        m = _DIFF_FILE.match(raw)
        if m:
            current = ChangedFile(path=m.group(2))
            diff.files.append(current)
            continue
        m = _NEW_FILE.match(raw)
        if m and current is not None:
            current.path = m.group(1)
            continue
        m = _HUNK.match(raw)
        if m:
            new_lineno = int(m.group(1))
            continue
        if current is None:
            continue
        if raw.startswith("+++") or raw.startswith("---"):
            continue
        if raw.startswith("+"):
            current.added_lines.append((new_lineno, raw[1:]))
            new_lineno += 1
        elif raw.startswith("-"):
            continue
        else:
            new_lineno += 1
    return diff


def git_diff(repo_root: str, base: str, head: str) -> Diff:
    result = subprocess.run(
        ["git", "diff", f"{base}...{head}"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    if result.returncode != 0:
        raise RuntimeError(f"git diff failed: {result.stderr.strip()}")
    return parse_unified_diff(result.stdout)
