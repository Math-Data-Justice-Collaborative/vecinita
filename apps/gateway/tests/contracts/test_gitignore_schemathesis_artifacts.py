"""Regression: Schemathesis CLI writes JUnit under apis/gateway/schemathesis-report/ (see schemathesis.toml).

``run_schemathesis_live.sh`` emits ``junit-gateway.xml`` there; the path must stay in the repo
``.gitignore`` so it is never committed accidentally.
"""

from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[4]
GITIGNORE = REPO_ROOT / ".gitignore"
_EXPECTED_PATTERN = "schemathesis-report/"

pytestmark = pytest.mark.unit


@pytest.mark.contract
def test_gitignore_lists_gateway_schemathesis_junit_report() -> None:
    assert GITIGNORE.is_file(), f"Missing root .gitignore at {GITIGNORE}"
    raw_lines = GITIGNORE.read_text(encoding="utf-8").splitlines()
    normalized = [ln.split("#", 1)[0].strip() for ln in raw_lines]
    assert (
        _EXPECTED_PATTERN in normalized
    ), f".gitignore must list {_EXPECTED_PATTERN!r} so Schemathesis output stays untracked."
