"""Regression coverage for LLM secret sync safety."""

from __future__ import annotations

import os
import stat
import subprocess
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
_SCRIPT = _REPO_ROOT / "scripts" / "deploy" / "sync_llm_secret.sh"
_BASH = Path("/bin/bash")


def _write_executable(path: Path, contents: str) -> None:
    _ = path.write_text(contents, encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR)


def test_sync_llm_secret_merge_fails_closed_without_live_export_or_adapter_env(
    tmp_path: Path,
) -> None:
    """A merge apply must not replace the GPU secret when adapter pins are unavailable.

    [Corpus: feature-list.md §F77]
    [Spec: docs/adr/ADR-053-modal-lora-finetune.md]
    [Spec: docs/staging-secrets-matrix.md §EV-027]
    """
    if not _BASH.is_file():
        return

    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    modal_log = tmp_path / "modal.log"
    repo_export = _REPO_ROOT / ".tmp" / "modal-vecinita-llm-gpu.env"
    if repo_export.exists():
        repo_export.unlink()

    _write_executable(
        bin_dir / "modal",
        """#!/usr/bin/env bash
set -euo pipefail
printf '%s\\n' "$*" >> "$MODAL_LOG"
if [[ "${1:-}" == "token" && "${2:-}" == "info" ]]; then
  echo "Workspace: vecinita"
  exit 0
fi
if [[ "${1:-}" == "secret" && "${2:-}" == "create" ]]; then
  if [[ "${3:-}" == "vecinita-llm-gpu" ]]; then
    echo "secret create should not run" >&2
    exit 99
  fi
  exit 0
fi
exit 0
""",
    )
    _write_executable(
        bin_dir / "uv",
        """#!/usr/bin/env bash
set -euo pipefail
exit 1
""",
    )

    env = {
        **os.environ,
        "PATH": f"{bin_dir}:{os.environ['PATH']}",
        "MODAL_LOG": str(modal_log),
        "MODAL_TOKEN_ID": "token-id",
        "MODAL_TOKEN_SECRET": "token-secret",
        "VECINITA_MODAL_PROXY_KEY": "proxy-key",
    }

    proc = subprocess.run(  # noqa: S603
        [str(_BASH), str(_SCRIPT), "--merge", "--apply"],
        cwd=_REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert proc.returncode == 1
    assert "Refusing to replace vecinita-llm-gpu" in proc.stderr
    if modal_log.exists():
        assert "secret create --force vecinita-llm-gpu" not in modal_log.read_text(encoding="utf-8")
