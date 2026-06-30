"""Regression: modal token info transient failures in CI must retry before failing."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
_MIN_TOKEN_INFO_CALLS = 2


def test_modal_ensure_workspace_retries_transient_token_info_failure(
    tmp_path: Path,
) -> None:
    """First modal token info calls fail; script retries and succeeds (deploy-preflight flake)."""
    counter = tmp_path / "token_info_calls"
    counter.write_text("0", encoding="utf-8")

    fake_modal = tmp_path / "modal"
    fake_modal.write_text(
        f"""#!/usr/bin/env bash
set -euo pipefail
COUNTER="{counter}"
if [[ "$1" == "token" && "$2" == "info" ]]; then
  n=$(cat "$COUNTER")
  n=$((n + 1))
  echo "$n" > "$COUNTER"
  if [[ "$n" -lt 2 ]]; then
    echo "transient Modal API error" >&2
    exit 1
  fi
  echo "Workspace: vecinita (ac-test)"
  exit 0
fi
if [[ "$1" == "profile" && "$2" == "current" ]]; then
  echo "default"
  exit 0
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
    env["MODAL_TOKEN_ID"] = "ak-test"  # noqa: S105 # test fixture value, not a real secret
    env["MODAL_TOKEN_SECRET"] = "as-test"  # noqa: S105 # test fixture value, not a real secret
    env["MODAL_TOKEN_INFO_RETRIES"] = "3"  # noqa: S105 # retry count, not a secret
    env["MODAL_TOKEN_INFO_RETRY_DELAY"] = "0"  # noqa: S105 # delay seconds, not a secret

    result = subprocess.run(
        ["bash", "-c", "source scripts/modal_ensure_workspace.sh"],  # noqa: S607
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "token auth" in result.stdout
    assert int(counter.read_text(encoding="utf-8")) >= _MIN_TOKEN_INFO_CALLS
