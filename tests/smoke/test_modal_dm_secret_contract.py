"""EV-006 F35 — Modal data-management secret contract (ADR-030 §1, TP-S005-01).

Offline checks that deploy scripts document SUPABASE_SECRET_KEY for /admin/users*.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
MODAL_ENV_EXAMPLE = REPO_ROOT / "infra" / "modal" / ".env.example"
SYNC_MODAL_SECRET = REPO_ROOT / "scripts" / "deploy" / "sync_modal_secret.sh"
DM_MODAL_APP = REPO_ROOT / "infra" / "modal" / "data_management_app.py"


def test_modal_env_example_documents_supabase_secret_key() -> None:
    """infra/modal/.env.example lists SUPABASE_SECRET_KEY for F35 admin routes."""
    text = MODAL_ENV_EXAMPLE.read_text(encoding="utf-8")
    assert "SUPABASE_SECRET_KEY" in text
    assert "/admin/users" in text or "Admin API" in text


def test_sync_modal_secret_script_includes_supabase_secret_key() -> None:
    """sync_modal_secret.sh pushes SUPABASE_SECRET_KEY when set in the shell."""
    text = SYNC_MODAL_SECRET.read_text(encoding="utf-8")
    assert "SUPABASE_SECRET_KEY" in text
    assert "EV-006" in text or "F35" in text


def test_data_management_modal_app_docstring_references_secret_key() -> None:
    """Modal ASGI entrypoint docstring documents the required admin API secret."""
    text = DM_MODAL_APP.read_text(encoding="utf-8")
    assert "SUPABASE_SECRET_KEY" in text
    assert "EV-006" in text or "F35" in text
