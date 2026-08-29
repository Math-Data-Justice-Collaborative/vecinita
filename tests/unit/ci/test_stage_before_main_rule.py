"""TC-298 / AC-ST8 — Stage before Main agent rule exists (EV-033 / F83)."""

from __future__ import annotations

from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
_RULE_PATH = _REPO_ROOT / ".cursor" / "rules" / "stage-before-main.mdc"


def test_stage_before_main_rule_exists_always_apply() -> None:
    """Rule file must exist with alwaysApply and required Stage→Main cites (TC-298)."""
    assert _RULE_PATH.is_file(), f"missing {_RULE_PATH.relative_to(_REPO_ROOT)}"
    text = _RULE_PATH.read_text(encoding="utf-8")
    assert "alwaysApply: true" in text
    assert "staging-smoke" in text
    assert "CI success" in text
    assert "F83" in text or "feature-list.md §F83" in text
    assert "ADR-054" in text
    assert "AskQuestion" in text
    assert "stage` branch" in text or "stage branch" in text.lower() or "`stage` branch" in text


def test_deploy_staging_workflow_names_staging_smoke_check() -> None:
    """Ruleset contract: deploy-staging.yml must expose staging-smoke job name (TC-297)."""
    workflow = _REPO_ROOT / ".github" / "workflows" / "deploy-staging.yml"
    assert workflow.is_file()
    body = workflow.read_text(encoding="utf-8")
    assert "staging-smoke" in body
