"""S027-D34 — remote CI runs unit + coverage; compose suites stay local."""

from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
CI_YML = REPO_ROOT / ".github" / "workflows" / "ci.yml"
COMMENT_SCRIPT = REPO_ROOT / "scripts" / "ci" / "comment_unit_coverage_pr.sh"


@pytest.mark.unit
def test_remote_python_job_runs_unit_only_not_compose_suites() -> None:
    """Remote python job must pytest tests/unit only (no integration/e2e/compose)."""
    text = CI_YML.read_text(encoding="utf-8")
    assert "uv run pytest tests/unit" in text
    # Full compose-backed suites must not be the remote python Pytest step.
    assert "tests/integration tests/privacy tests/e2e tests/smoke tests/eval tests/bugs" not in text
    # Local full suite remains documented / available via make test-py path elsewhere.
    assert "ruff check" in text
    assert "ruff format --check" in text
    assert "basedpyright" in text


@pytest.mark.unit
def test_coverage_job_posts_markdown_pr_comment() -> None:
    """Coverage job writes markdown and upserts a sticky PR comment."""
    text = CI_YML.read_text(encoding="utf-8")
    assert "--markdown-out" in text
    assert "comment_unit_coverage_pr.sh" in text
    assert COMMENT_SCRIPT.is_file()
    script = COMMENT_SCRIPT.read_text(encoding="utf-8")
    assert "vecinita-unit-coverage" in script
    assert "gh api" in script or "gh pr comment" in script
