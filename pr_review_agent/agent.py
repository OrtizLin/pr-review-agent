from __future__ import annotations

from dataclasses import dataclass

from .config import Config
from .git_tools import Diff
from .prompts import PROMPT_VERSION, REVIEW_PROMPT_TEMPLATE, SYSTEM_PROMPT
from .tools import retrieve_guidelines, run_lint, run_tests


@dataclass
class Finding:
    file: str
    line: int
    severity: str  # blocker | major | minor
    title: str
    evidence: str
    suggestion: str

    def to_dict(self) -> dict:
        return {
            "file": self.file,
            "line": self.line,
            "severity": self.severity,
            "title": self.title,
            "evidence": self.evidence,
            "suggestion": self.suggestion,
        }


# Deterministic rules for the offline dry-run reviewer. Each rule maps to
# a guideline in docs/guidelines.md, so a finding always has a source.
_RULES = [
    ("bare except", "except:", "major", "Bare except hides real errors",
     "Catch a specific exception and log it."),
    ("print in production code", "print(", "minor", "Leftover print statement",
     "Use logging instead of print."),
    ("TODO left in diff", "TODO", "minor", "Unresolved TODO in new code",
     "Resolve it or file a tracked issue and reference it."),
    ("hardcoded secret hint", "password =", "blocker", "Possible hardcoded secret",
     "Move the secret to env / secret manager and rotate it."),
]


def review_with_llm(prompt: str) -> list[Finding]:
    """LLM path: prompt -> model JSON -> Finding, then validated by the caller.

    The model output is parsed strictly in llm.parse_llm_response() and
    re-checked in validate_findings(), so it cannot invent files/lines.
    Without LLM_API_KEY this raises a clear error instead of faking a review.
    """
    from .llm import complete_review

    from .prompts import SYSTEM_PROMPT

    items = complete_review(SYSTEM_PROMPT, prompt)
    return [Finding(**item) for item in items]


def draft_findings(diff: Diff) -> list[Finding]:
    findings: list[Finding] = []
    for changed in diff.files:
        for lineno, line in changed.added_lines:
            for _name, needle, severity, title, suggestion in _RULES:
                if needle in line:
                    findings.append(
                        Finding(
                            file=changed.path,
                            line=lineno,
                            severity=severity,
                            title=title,
                            evidence=line.strip(),
                            suggestion=suggestion,
                        )
                    )
    return findings


def validate_findings(diff: Diff, findings: list[Finding]) -> list[Finding]:
    """Drop any finding that does not point at an added line.

    This is the anti-hallucination gate: the agent may not invent files
    or lines, even when an LLM draft does.
    """
    valid: dict[tuple[str, int], str] = {}
    for changed in diff.files:
        for lineno, line in changed.added_lines:
            valid[(changed.path, lineno)] = line.strip()
    kept = []
    for f in findings:
        if (f.file, f.line) in valid and f.severity in {"blocker", "major", "minor"}:
            kept.append(f)
    return kept


def run_agent(diff: Diff, config: Config) -> dict:
    tool_results = (
        f"lint: {run_lint(config.repo_root)}\n"
        f"tests: {run_tests(config.repo_root, config.test_timeout_seconds)}"
    )
    guidelines = retrieve_guidelines(config, diff.text())
    prompt = REVIEW_PROMPT_TEMPLATE.format(
        guidelines=guidelines, tool_results=tool_results, diff=diff.text()
    )
    if config.dry_run:
        findings = draft_findings(diff)
    else:
        findings = review_with_llm(prompt)
    findings = validate_findings(diff, findings)[: config.max_findings]
    return {
        "prompt_version": PROMPT_VERSION,
        "system_prompt": SYSTEM_PROMPT,
        "tool_results": tool_results,
        "findings": [f.to_dict() for f in findings],
        "finding_count": len(findings),
        "human_approval_required": True,
    }
