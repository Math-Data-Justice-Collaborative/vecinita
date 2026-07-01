"""CI deploy env materialization (scripts/deploy/ci_materialize_env.sh)."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SCRIPT = _REPO_ROOT / "scripts" / "deploy" / "ci_materialize_env.sh"
_BASH = Path("/bin/bash")


def test_ci_materialize_env_derives_vite_and_cors_aliases() -> None:
    """Materialize maps Supabase and frontend URLs into deploy aliases."""
    if not _BASH.is_file():
        return
    env = {
        **os.environ,
        "SUPABASE_URL": "https://example.supabase.co",
        "SUPABASE_PUBLISHABLE_KEY": "sb_publishable_test",
        "VECINITA_INTERNAL_API_KEY": "internal-key",
        "VECINITA_MODAL_PROXY_KEY": "proxy-key",
        "VECINITA_STAGING_WRITE_URL": "https://write.example",
        "VECINITA_STAGING_ADMIN_FRONTEND_URL": "https://admin.example",
        "VECINITA_STAGING_CHAT_FRONTEND_URL": "https://chat.example",
    }
    cmd = (
        f"set -a && source '{_SCRIPT}' && "
        "echo VITE_SUPABASE_URL=$VITE_SUPABASE_URL && "
        "echo VECINITA_CORS_ORIGINS=$VECINITA_CORS_ORIGINS"
    )
    proc = subprocess.run(  # noqa: S603
        [str(_BASH), "-c", cmd],
        cwd=_REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )
    assert "VITE_SUPABASE_URL=https://example.supabase.co" in proc.stdout
    assert "VECINITA_CORS_ORIGINS=https://admin.example,https://chat.example" in proc.stdout


def test_ci_materialize_env_check_alembic_requires_database_url() -> None:
    """Alembic check fails when DATABASE_URL is unset."""
    if not _BASH.is_file():
        return
    env = {k: v for k, v in os.environ.items() if k != "DATABASE_URL"}
    proc = subprocess.run(  # noqa: S603
        [str(_BASH), str(_SCRIPT), "--check", "alembic"],
        cwd=_REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 1
    assert "DATABASE_URL" in proc.stderr
