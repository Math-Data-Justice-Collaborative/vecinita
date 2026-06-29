"""EV-005 F34 — Supabase CI pipeline contract (ADR-027 §6).

Validates repo-managed Supabase CI artifacts without requiring Docker or cloud credentials.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "supabase.yml"
CONFIG_CHECK = REPO_ROOT / "scripts" / "check_supabase_config.sh"
CI_SYNC = REPO_ROOT / "scripts" / "supabase" / "ci_sync.sh"
CONFIG_TOML = REPO_ROOT / "supabase" / "config.toml"
CANONICAL_PROJECT_REF = "cfuvghdsuwactfeamtym"


def _workflow_text() -> str:
    assert WORKFLOW_PATH.is_file(), f"missing workflow: {WORKFLOW_PATH}"
    return WORKFLOW_PATH.read_text(encoding="utf-8")


def test_supabase_workflow_exists_with_validate_and_sync_jobs() -> None:
    """Supabase CI defines offline validate plus secret-gated remote sync jobs."""
    text = _workflow_text()
    assert "validate:" in text
    assert "sync-production:" in text
    assert "preview-branch:" in text


def test_supabase_workflow_uses_setup_cli_and_path_filters() -> None:
    """Workflow is path-filtered and installs Supabase CLI via the official action."""
    text = _workflow_text()
    assert "supabase/**" in text
    assert "supabase/setup-cli@v1" in text
    assert "bash scripts/check_supabase_config.sh" in text


def test_supabase_config_check_script_exists() -> None:
    """Offline config guard script is present for local parity and CI validate job."""
    assert CONFIG_CHECK.is_file()


def test_supabase_ci_sync_script_exists() -> None:
    """Remote sync helper exists for secret-gated production/preview steps."""
    assert CI_SYNC.is_file()


def test_supabase_config_toml_invite_only_and_canonical_project() -> None:
    """config.toml disables public signup and pins the canonical project ref."""
    text = CONFIG_TOML.read_text(encoding="utf-8")
    assert f'project_id = "{CANONICAL_PROJECT_REF}"' in text
    assert "enable_signup = false" in text


def test_sync_production_job_gated_on_main_and_secrets() -> None:
    """Production sync runs only on main pushes; token detection happens in a step."""
    text = _workflow_text()
    assert "refs/heads/main" in text
    assert "Detect Supabase access token" in text
    assert "sync-production:" in text
