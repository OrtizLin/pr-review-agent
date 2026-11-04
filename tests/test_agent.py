from pathlib import Path

from pr_review_agent.agent import draft_findings, run_agent, validate_findings
from pr_review_agent.config import Config
from pr_review_agent.git_tools import parse_unified_diff


def sample_diff():
    text = (Path(__file__).parent.parent / "examples" / "sample_diff.diff").read_text()
    return parse_unified_diff(text)


def test_parse_diff_only_counts_added_lines():
    diff = sample_diff()
    assert diff.paths == {"examples/sample_repo/app.py"}
    assert len(diff.files[0].added_lines) >= 5


def test_dry_run_finds_bare_except_and_secret():
    findings = draft_findings(sample_diff())
    titles = [f.title for f in findings]
    assert "Bare except hides real errors" in titles
    assert "Possible hardcoded secret" in titles


def test_validation_drops_invented_files():
    from pr_review_agent.agent import Finding

    diff = sample_diff()
    bad = Finding(file="nope.py", line=1, severity="major",
                  title="Invented", evidence="x", suggestion="y")
    assert validate_findings(diff, [bad]) == []


def test_run_agent_reports_human_approval(tmp_path):
    config = Config(repo_root=tmp_path, dry_run=True)
    result = run_agent(sample_diff(), config)
    assert result["human_approval_required"] is True
    assert result["finding_count"] >= 3
