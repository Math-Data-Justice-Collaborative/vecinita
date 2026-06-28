"""Regression: deploy-preflight modal-secrets must not call profile activate in CI."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_modal_ensure_workspace_uses_token_auth_without_named_profile(
    tmp_path: Path,
) -> None:
    """MODAL_TOKEN_* env auth has no vecinita profile in ~/.modal.toml (GitHub Actions)."""
    fake_modal = tmp_path / "modal"
    fake_modal.write_text(
        """#!/usr/bin/env bash
set -euo pipefail
if [[ "$1" == "token" && "$2" == "info" ]]; then
  echo "Workspace: vecinita (ac-test)"
  exit 0
fi
if [[ "$1" == "profile" && "$2" == "current" ]]; then
  echo "default"
  exit 0
fi
if [[ "$1" == "profile" && "$2" == "activate" ]]; then
  echo "profile activate must not run in CI token mode" >&2
  exit 1
fi
echo "unexpected: $*" >&2
exit 1
""",
        encoding="utf-8",
    )
    fake_modal.chmod(0o755)

    env = os.environ.copy()
    env["PATH"] = f"{tmp_path}:{env.get('PATH', '')}"
    env["HOME"] = str(tmp_path / "home")
    env["MODAL_TOKEN_ID"] = "ak-test"
    env["MODAL_TOKEN_SECRET"] = "as-test"

    result = subprocess.run(
        ["bash", "-c", "source scripts/modal_ensure_workspace.sh"],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "token auth" in result.stdout
    assert "profile activate must not run" not in result.stderr
