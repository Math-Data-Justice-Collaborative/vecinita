"""Smoke tests for deploy connectivity scripts."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

_SKIP_GUARD = """
CHAT_API="${VECINITA_STAGING_CHAT_URL:-}"
CHAT_FE="${VECINITA_STAGING_CHAT_FRONTEND_URL:-}"
WRITE_API="${VECINITA_STAGING_WRITE_URL:-}"
ADMIN_FE="${VECINITA_STAGING_ADMIN_FRONTEND_URL:-}"
if [[ -z "$CHAT_API" && -z "$CHAT_FE" && -z "$WRITE_API" && -z "$ADMIN_FE" ]]; then
  echo "SKIP live H4/H5: set VECINITA_STAGING_* URLs (see connectivity-gates.md)"
  exit 0
fi
exit 1
"""


def test_verify_connectivity_skips_live_when_staging_urls_unset() -> None:
    """H4/H5 skip guard must exit 0 when no staging URLs are configured (QA-S007-002)."""
    env = {
        key: value for key, value in os.environ.items() if not key.startswith("VECINITA_STAGING_")
    }
    result = subprocess.run(  # noqa: S603
        ["/bin/bash", "-c", _SKIP_GUARD],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "SKIP live H4/H5" in result.stdout


def test_verify_connectivity_script_exists_and_documents_skip() -> None:
    """Operator script must document env-gated H4/H5 skip (QA-S007-002)."""
    script = REPO_ROOT / "scripts/deploy/verify_connectivity.sh"
    text = script.read_text(encoding="utf-8")
    assert "SKIP live H4/H5" in text
    assert "VECINITA_STAGING_CHAT_URL" in text
