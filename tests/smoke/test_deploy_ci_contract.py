"""Deploy CI/CD contract — Modal, Supabase, DigitalOcean, Resend (via Supabase SMTP).

Ensures production deploy workflows exist, declare required secrets, and follow the
EV-007 redeploy order: Supabase config push → Modal → DigitalOcean.
Resend has no standalone deploy target; delivery is configured through Supabase
`config push` (`SUPABASE_SMTP_PASS`) and Modal operator secrets (`RESEND_API_KEY`).
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

WORKFLOWS = {
    "ci": REPO_ROOT / ".github/workflows/ci.yml",
    "supabase": REPO_ROOT / ".github/workflows/supabase.yml",
    "deploy_preflight": REPO_ROOT / ".github/workflows/deploy-preflight.yml",
    "deploy_modal": REPO_ROOT / ".github/workflows/deploy-modal.yml",
    "deploy_digitalocean": REPO_ROOT / ".github/workflows/deploy-digitalocean.yml",
}


def _read(name: str) -> str:
    path = WORKFLOWS[name]
    assert path.is_file(), f"missing workflow: {path}"
    return path.read_text(encoding="utf-8")


def test_all_deploy_workflows_exist() -> None:
    """Every production deploy surface has a GitHub Actions workflow file."""
    for path in WORKFLOWS.values():
        assert path.is_file(), f"missing workflow: {path}"


def test_deploy_modal_chained_after_ci() -> None:
    """Modal deploy runs only after CI succeeds on main (or manual dispatch)."""
    text = _read("deploy_modal")
    assert 'workflows: ["CI"]' in text
    assert "workflow_run:" in text
    assert "workflow_dispatch" in text
    assert "head_branch == 'main'" in text


def test_deploy_modal_includes_supabase_sync_before_deploy() -> None:
    """EV-007 order: Supabase config/migrations push before Modal deploy."""
    text = _read("deploy_modal")
    assert "supabase-sync:" in text
    assert "needs: supabase-sync" in text
    assert "bash scripts/supabase/ci_sync.sh sync-production" in text


def test_deploy_digitalocean_chained_after_modal() -> None:
    """DO deploy runs after Modal deploy succeeds on main (or manual dispatch)."""
    text = _read("deploy_digitalocean")
    assert 'workflows: ["Deploy Modal"]' in text
    assert "workflow_run:" in text
    assert "workflow_dispatch" in text


def test_supabase_sync_production_passes_resend_smtp_secret() -> None:
    """Supabase sync-production resolves env(SUPABASE_SMTP_PASS) for Resend SMTP."""
    text = _read("supabase")
    assert "sync-production:" in text
    assert "SUPABASE_SMTP_PASS: ${{ secrets.SUPABASE_SMTP_PASS }}" in text


def test_supabase_preview_branch_passes_resend_smtp_secret() -> None:
    """Preview branches also receive SUPABASE_SMTP_PASS for config push."""
    text = _read("supabase")
    preview_start = text.index("preview-branch:")
    sync_start = text.index("sync-production:")
    for section in (text[preview_start:sync_start], text[sync_start:]):
        assert "SUPABASE_SMTP_PASS: ${{ secrets.SUPABASE_SMTP_PASS }}" in section


def test_deploy_modal_declares_platform_secrets() -> None:
    """Modal CD requires Modal tokens; Supabase sync uses Supabase secrets."""
    text = _read("deploy_modal")
    assert "MODAL_TOKEN_ID: ${{ secrets.MODAL_TOKEN_ID }}" in text
    assert "MODAL_TOKEN_SECRET: ${{ secrets.MODAL_TOKEN_SECRET }}" in text
    assert "SUPABASE_ACCESS_TOKEN: ${{ secrets.SUPABASE_ACCESS_TOKEN }}" in text
    assert "SUPABASE_SMTP_PASS: ${{ secrets.SUPABASE_SMTP_PASS }}" in text


def test_deploy_digitalocean_declares_do_token() -> None:
    """DigitalOcean CD requires DIGITALOCEAN_TOKEN."""
    text = _read("deploy_digitalocean")
    assert "DIGITALOCEAN_TOKEN: ${{ secrets.DIGITALOCEAN_TOKEN }}" in text


def test_deploy_modal_deploys_all_three_apps() -> None:
    """Modal CD deploys embedding, data-management, and llm apps."""
    text = _read("deploy_modal")
    assert "bash scripts/deploy/modal.sh" in text


def test_deploy_digitalocean_deploys_all_four_apps() -> None:
    """DO CD deploys internal-write-api, chat-rag-backend, and both frontends."""
    text = _read("deploy_digitalocean")
    for app in (
        "vecinita-internal-write-api",
        "vecinita-chat-rag-backend",
        "vecinita-chat-rag-frontend",
        "vecinita-admin-frontend",
    ):
        assert app in text


def test_resend_has_no_standalone_deploy_workflow() -> None:
    """Resend is configured via Supabase SMTP + Modal secrets, not its own workflow."""
    workflow_dir = REPO_ROOT / ".github/workflows"
    for path in workflow_dir.glob("*.yml"):
        name = path.name.lower()
        assert "resend" not in name, f"unexpected Resend workflow: {path.name}"
    supabase_text = _read("supabase")
    assert "smtp.resend.com" not in supabase_text  # host lives in config.toml, not workflow
    config = (REPO_ROOT / "supabase/config.toml").read_text(encoding="utf-8")
    assert "smtp.resend.com" in config
