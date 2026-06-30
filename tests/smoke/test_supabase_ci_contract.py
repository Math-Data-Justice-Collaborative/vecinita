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
SUPABASE_DIR = REPO_ROOT / "supabase"
CANONICAL_PROJECT_REF = "cfuvghdsuwactfeamtym"

# EV-006 F35 — email template blocks (TP-S005-08, #5124).
# auth.email.template.* content_path resolves from the **project root**.
ROOT_RELATIVE_TEMPLATES = {
    "invite": "supabase/templates/invite.html",
    "recovery": "supabase/templates/recovery.html",
    "confirmation": "supabase/templates/confirmation.html",
    "magic_link": "supabase/templates/magic_link.html",
    "email_change": "supabase/templates/email_change.html",
}
# auth.email.notification.* content_path resolves from the **supabase/** directory.
SUPABASE_RELATIVE_TEMPLATES = {
    "password_changed": "templates/password-changed.html",
}


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


# --- EV-006 F35: Resend SMTP + versioned email templates (TC-094, TC-095) ---


def test_resend_smtp_enabled_with_env_password_placeholder() -> None:
    """[auth.email.smtp] uses Resend host/port/user and an env() password (TC-094)."""
    text = CONFIG_TOML.read_text(encoding="utf-8")
    assert "[auth.email.smtp]" in text
    assert "enabled = true" in text
    assert 'host = "smtp.resend.com"' in text
    assert "port = 465" in text
    assert 'user = "resend"' in text
    assert 'pass = "env(SUPABASE_SMTP_PASS)"' in text
    # No literal Resend API key may be committed (keys appear as a quoted "re_..." token).
    assert '"re_' not in text


def test_email_rate_limits_and_password_policy() -> None:
    """Email rate-limit, OTP expiry, cooldown, and password policy are pinned (TC-094)."""
    text = CONFIG_TOML.read_text(encoding="utf-8")
    assert "email_sent = 30" in text
    assert "otp_expiry = 3600" in text
    assert 'max_frequency = "60s"' in text
    assert "minimum_password_length = 8" in text


def test_email_template_blocks_declare_content_paths() -> None:
    """All six template/notification blocks declare their content_path (TC-094)."""
    text = CONFIG_TOML.read_text(encoding="utf-8")
    for name, path in ROOT_RELATIVE_TEMPLATES.items():
        assert f"[auth.email.template.{name}]" in text, f"missing template block {name}"
        assert f'content_path = "{path}"' in text, f"missing content_path for {name}"
    for name, path in SUPABASE_RELATIVE_TEMPLATES.items():
        assert f"[auth.email.notification.{name}]" in text, f"missing notification {name}"
        assert f'content_path = "{path}"' in text, f"missing content_path for {name}"


def test_template_html_files_exist_and_are_stacked_bilingual() -> None:
    """Each referenced template exists and contains EN and ES sections (TC-094)."""
    for path in ROOT_RELATIVE_TEMPLATES.values():
        html = (REPO_ROOT / path).read_text(encoding="utf-8")
        assert "<!-- lang:en -->" in html, f"{path} missing EN section marker"
        assert "<!-- lang:es -->" in html, f"{path} missing ES section marker"
        assert "{{ .ConfirmationURL }}" in html, f"{path} missing confirmation URL token"
    for path in SUPABASE_RELATIVE_TEMPLATES.values():
        html = (SUPABASE_DIR / path).read_text(encoding="utf-8")
        assert "<!-- lang:en -->" in html, f"{path} missing EN section marker"
        assert "<!-- lang:es -->" in html, f"{path} missing ES section marker"


def test_template_path_resolution_convention() -> None:
    """template.* resolves from repo root; notification.* from supabase/ (#5124, TC-095)."""
    for path in ROOT_RELATIVE_TEMPLATES.values():
        assert (REPO_ROOT / path).is_file(), f"root-relative template missing: {path}"
        # The notification (supabase-relative) base must NOT also resolve these.
        assert path.startswith("supabase/")
    for path in SUPABASE_RELATIVE_TEMPLATES.values():
        assert (SUPABASE_DIR / path).is_file(), f"supabase-relative template missing: {path}"
        assert not path.startswith("supabase/")


def test_supabase_cli_pinned_for_template_push() -> None:
    """Workflow pins a CLI version supporting template HTML push (>=2.70,<3; TC-094)."""
    text = _workflow_text()
    assert 'version: "latest"' not in text
    assert "version: latest" not in text
    assert ">=2.70,<3" in text


def test_config_check_script_enforces_smtp_and_template_contract() -> None:
    """Offline guard enforces the Resend SMTP + template path contract (TC-094/095)."""
    script = CONFIG_CHECK.read_text(encoding="utf-8")
    assert "smtp.resend.com" in script
    assert "SUPABASE_SMTP_PASS" in script
    assert "supabase/templates/" in script
    assert "templates/password-changed.html" in script
