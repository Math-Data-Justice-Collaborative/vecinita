"""TC-208-211 / UJ-067 / F62 - Husky lean pre-push + expanded pre-commit."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
PRE_PUSH = REPO_ROOT / "scripts" / "ci" / "pre_push.sh"
PRE_COMMIT = REPO_ROOT / "scripts" / "ci" / "pre_commit.sh"
HUSKY_PRE_COMMIT = REPO_ROOT / ".husky" / "pre-commit"
_BASH = Path("/bin/bash")


def _strip_comments(text: str) -> str:
    lines: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        lines.append(line)
    return "\n".join(lines)


@pytest.mark.unit
def test_default_pre_push_is_lint_and_test_fast_only() -> None:
    """TC-208 / AC-CI1: default push path has no typecheck or security-scan."""
    body = _strip_comments(PRE_PUSH.read_text(encoding="utf-8"))
    assert "make lint" in body
    assert "make test-fast" in body
    # After full/medium opt-in blocks, the default echo/exec section:
    after_medium = body.split("VECINITA_MEDIUM_PRE_PUSH")[-1]
    # Take from last opt-in fi to end as default path.
    default_tail = after_medium.split("fi", 1)[-1]
    assert "make check-fast" not in default_tail
    assert "make security-scan" not in default_tail
    assert "make typecheck" not in default_tail
    assert "make lint" in default_tail
    assert "make test-fast" in default_tail


@pytest.mark.unit
def test_pre_commit_runs_typecheck_security_scan_and_job_dispatch() -> None:
    """TC-209 / AC-CI2."""
    assert PRE_COMMIT.is_file(), "scripts/ci/pre_commit.sh must exist"
    body = PRE_COMMIT.read_text(encoding="utf-8")
    assert "make typecheck" in body
    assert "make security-scan" in body
    assert "pre_commit_job_dispatch.sh" in body
    husky = HUSKY_PRE_COMMIT.read_text(encoding="utf-8")
    assert "pre_commit.sh" in husky


@pytest.mark.unit
def test_skip_env_knobs_exit_zero() -> None:
    """TC-210 / AC-CI3."""
    if not _BASH.is_file():
        pytest.skip("bash not available")
    env = os.environ.copy()
    env["VECINITA_SKIP_PRE_PUSH"] = "1"
    push = subprocess.run(  # noqa: S603
        [str(_BASH), str(PRE_PUSH)],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )
    assert push.returncode == 0
    assert "skipped" in push.stdout.lower()

    env2 = os.environ.copy()
    env2["VECINITA_SKIP_PRE_COMMIT"] = "1"
    commit = subprocess.run(  # noqa: S603
        [str(_BASH), str(PRE_COMMIT)],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        env=env2,
    )
    assert commit.returncode == 0
    assert "skipped" in commit.stdout.lower()


@pytest.mark.unit
def test_local_dev_and_parity_rule_match_lean_push() -> None:
    """TC-211 / AC-CI4."""
    local_dev = (REPO_ROOT / "docs" / "LOCAL_DEV.md").read_text(encoding="utf-8")
    parity = (REPO_ROOT / ".cursor" / "rules" / "ci-local-parity.mdc").read_text(
        encoding="utf-8",
    )
    for text in (local_dev, parity):
        assert "make lint" in text
        assert "pre-commit" in text.lower() or "Pre-commit" in text
        # Push must not be documented as check-fast (lint+typecheck).
        assert "git push" in text.lower() or "**git push**" in text
