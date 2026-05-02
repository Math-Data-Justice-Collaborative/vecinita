"""Regression: Schemathesis CLI writes JUnit under apis/gateway/schemathesis-report/ (see schemathesis.toml).

``run_schemathesis_live.sh`` emits ``junit-gateway.xml`` there; the path must stay in the repo
``.gitignore`` so it is never committed accidentally.
"""

from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[4]
GITIGNORE = REPO_ROOT / ".gitignore"
_EXPECTED_LINE = "apis/gateway/schemathesis-report/junit-gateway.xml"

pytestmark = pytest.mark.unit


@pytest.mark.contract
def test_gitignore_lists_gateway_schemathesis_junit_report() -> None:
    assert GITIGNORE.is_file(), f"Missing root .gitignore at {GITIGNORE}"
    raw_lines = GITIGNORE.read_text(encoding="utf-8").splitlines()
    normalized = [ln.split("#", 1)[0].strip() for ln in raw_lines]
    assert (
        _EXPECTED_LINE in normalized
    ), f".gitignore must list {_EXPECTED_LINE!r} so gateway Schemathesis JUnit output stays untracked."
