"""Tests for shell_deploy_guard Cursor hook."""

from __future__ import annotations

import sys
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parents[2] / ".cursor" / "hooks"
sys.path.insert(0, str(HOOKS_DIR))

from shell_deploy_guard import check_shell_command  # noqa: E402


def test_warns_prod_env_before_pytest() -> None:
    """Sourcing prod.env before pytest triggers corpus safety note."""
    notes = check_shell_command("set -a && source prod.env && set +a && pytest tests/unit")
    assert any("corpus-db-safety" in n for n in notes)


def test_warns_do_sync_follow_up() -> None:
    """DO secret sync reminds agent to verify and redeploy."""
    notes = check_shell_command("uv run scripts/deploy/do_apps.py sync-all-secrets")
    assert any("do-secrets-sync" in n for n in notes)


def test_warns_fontface_modal_prefix() -> None:
    """fontface-- in command triggers modal URL note."""
    notes = check_shell_command(
        "export VECINITA_MODAL_EMBED_URL=https://fontface--vecinita-embedding.modal.run"
    )
    assert any("fontface--" in n for n in notes)


def test_quiet_for_benign_command() -> None:
    """Unrelated shell commands produce no notes."""
    assert check_shell_command("uv run ruff check apps") == []
