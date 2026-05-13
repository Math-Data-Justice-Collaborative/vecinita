"""Regression tests for ``scripts/check_modal_http_ban.py`` (SC-005 / FR-001)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[4]
SCRIPT = REPO_ROOT / "scripts" / "check_modal_http_ban.py"


@pytest.mark.unit
def test_check_modal_http_ban_exits_zero_on_clean_tree() -> None:
    """Full-repo scan must pass; fails loudly when new Modal HTTP URL violations appear."""
    proc = subprocess.run(
        [sys.executable, str(SCRIPT)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
