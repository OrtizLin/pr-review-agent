from dataclasses import dataclass
from pathlib import Path


@dataclass
class Config:
    repo_root: Path = Path(".")
    guidelines_dir: Path = Path("docs")
    dry_run: bool = True
    max_findings: int = 20
    test_timeout_seconds: int = 120
