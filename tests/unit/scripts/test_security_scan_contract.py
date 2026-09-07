"""Security scan contract guards for local secret ignores.

[Corpus: feature-list.md §F62]
[Corpus: tests]
[Spec: docs/security/static-analysis.md]
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
RUN_ALL = REPO_ROOT / "scripts" / "security" / "run-all.sh"
KICS_EXCLUDES = REPO_ROOT / "config" / "security" / "kics-exclude-queries.txt"


def test_2ms_ignores_gitignored_local_secret_files() -> None:
    """2ms local runs should skip gitignored operator secret files."""
    text = RUN_ALL.read_text(encoding="utf-8")

    for pattern in (
        "--ignore-pattern '.env.*'",
        "--ignore-pattern '.staging-*.local'",
    ):
        assert pattern in text


def test_kics_excludes_local_postgres_capability_noise() -> None:
    """Local dev Postgres compose must not hard-fail on the capability query."""
    text = KICS_EXCLUDES.read_text(encoding="utf-8")

    assert "ce76b7d0-9e77-464d-b86f-c5c48e03e22d" in text
