"""EV-027 ship-path deploy contract for automations, freshness, and finetune.

[Corpus: feature-list.md §F78]
[Corpus: feature-list.md §F79]
[Corpus: feature-list.md §F80]
[Spec: docs/adr/ADR-052-corpus-automation-orchestration.md]
[Spec: docs/adr/ADR-053-modal-lora-finetune.md]
[Spec: docs/deployment-integration.md §EV-027]
[Spec: docs/staging-secrets-matrix.md]
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def _read(*parts: str) -> str:
    return (REPO_ROOT.joinpath(*parts)).read_text(encoding="utf-8")


def test_modal_cd_includes_finetune_secret_and_app() -> None:
    """Modal CD ships the separate FT app and its secret path."""
    workflow = _read(".github", "workflows", "deploy-modal.yml")
    assert "scripts/deploy/sync_finetune_secret.sh --apply" in workflow
    assert "VECINITA_FINETUNE_ENABLED: ${{ secrets.VECINITA_FINETUNE_ENABLED }}" in workflow
    assert "VECINITA_FINETUNE_ADAPTER_ID: ${{ secrets.VECINITA_FINETUNE_ADAPTER_ID }}" in workflow

    modal_sh = _read("scripts", "deploy", "modal.sh")
    assert "infra/modal/finetune_app.py" in modal_sh

    verify_build = _read("scripts", "deploy", "verify_build.sh")
    assert "infra/modal/finetune_app.py" in verify_build

    verify_secrets = _read("scripts", "deploy", "verify_secrets.sh")
    assert "vecinita-llm-finetune" in verify_secrets
    assert "llm-finetune-adapters" in verify_secrets


def test_do_cd_and_secret_sync_surface_ev027_envs() -> None:
    """DO rollout exposes EV-027 env families on the write API path."""
    workflow = _read(".github", "workflows", "deploy-digitalocean.yml")
    assert "VECINITA_AUTOMATIONS_ENABLED: ${{ secrets.VECINITA_AUTOMATIONS_ENABLED }}" in workflow
    assert "VECINITA_FRESHNESS_ENABLED: ${{ secrets.VECINITA_FRESHNESS_ENABLED }}" in workflow
    assert "VECINITA_FINETUNE_ENABLED: ${{ secrets.VECINITA_FINETUNE_ENABLED }}" in workflow

    github_sync = _read("scripts", "deploy", "sync_github_secrets.sh")
    assert "VECINITA_AUTOMATIONS_ENABLED" in github_sync
    assert "VECINITA_FRESHNESS_ENABLED" in github_sync
    assert "VECINITA_FINETUNE_ENABLED" in github_sync
    assert "VECINITA_FINETUNE_ADAPTER_ID" in github_sync
    assert "VECINITA_PLAYGROUND_FINETUNE_ADAPTER_ID" in github_sync

    do_apps = _read("scripts", "deploy", "do_apps.py")
    assert '"VECINITA_AUTOMATIONS_ENABLED"' in do_apps
    assert '"VECINITA_FRESHNESS_ENABLED"' in do_apps
    assert '"VECINITA_FINETUNE_ENABLED"' in do_apps

    do_spec = _read("infra", "do", "internal-write-api.yaml")
    assert "VECINITA_AUTOMATIONS_ENABLED" in do_spec
    assert 'value: "false"' in do_spec
    assert "VECINITA_FRESHNESS_STALE_DAYS" in do_spec
    assert 'value: "30"' in do_spec
    assert "VECINITA_FINETUNE_REQUIRE_APPROVE" in do_spec
    assert 'value: "true"' in do_spec


def test_sync_scripts_cover_finetune_secret_and_adapter_pins() -> None:
    """Operator and CI sync helpers include the FT secret and LLM adapter pins."""
    sync_env = _read("scripts", "deploy", "sync_env.sh")
    assert "sync_finetune_secret.sh" in sync_env

    sync_llm = _read("scripts", "deploy", "sync_llm_secret.sh")
    assert "VECINITA_FINETUNE_ADAPTER_ID" in sync_llm
    assert "VECINITA_PLAYGROUND_FINETUNE_ADAPTER_ID" in sync_llm

    modal_env = _read("infra", "modal", ".env.example")
    assert "sync_finetune_secret.sh" in modal_env
    assert "VECINITA_FINETUNE_ADAPTER_ID" in modal_env
    assert "VECINITA_PLAYGROUND_FINETUNE_ADAPTER_ID" in modal_env


def test_llm_secret_sync_preserves_live_adapter_pins() -> None:
    """CI/operator sync must merge live GPU keys before re-pushing the LLM secret.

    [Corpus: feature-list.md §F77]
    [Spec: docs/adr/ADR-053-modal-lora-finetune.md]
    [Spec: docs/staging-secrets-matrix.md §EV-027]
    """
    workflow = _read(".github", "workflows", "deploy-modal.yml")
    assert "bash scripts/deploy/sync_llm_secret.sh --merge --apply" in workflow
    # Gate like data-management sync — do not fail CD when LLM env is incomplete.
    assert "ci_materialize_env.sh --check modal" in workflow
    llm_step_idx = workflow.index("Sync Modal vecinita-llm secret")
    llm_slice = workflow[llm_step_idx : llm_step_idx + 500]
    assert "ci_materialize_env.sh --check modal" in llm_slice
    assert "skipping LLM secret sync" in llm_slice

    sync_llm = _read("scripts", "deploy", "sync_llm_secret.sh")
    assert "--merge" in sync_llm
    assert "reading live ${secret_name} secret to preserve existing keys" in sync_llm
    assert 'MODAL_SECRET_EXPORT_NAME="$secret_name"' in sync_llm
    assert "modal-${secret_name}.env" in sync_llm

    sync_env = _read("scripts", "deploy", "sync_env.sh")
    assert "bash scripts/deploy/sync_llm_secret.sh --merge --apply" in sync_env
