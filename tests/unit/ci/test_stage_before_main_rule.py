"""TC-298 / AC-ST8 — Stage before Main agent rule + CI stage hop (EV-033 / EV-036-D15 / F83)."""

from __future__ import annotations

from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
_RULE_PATH = _REPO_ROOT / ".cursor" / "rules" / "stage-before-main.mdc"
_CI_WORKFLOW = _REPO_ROOT / ".github" / "workflows" / "ci.yml"


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
    assert "EV-036-D15" in text
    assert "origin/stage" in text
    assert "base = `stage`" in text or 'base = "stage"' in text or "base = stage" in text


def test_ci_workflow_includes_stage_branch() -> None:
    """Feature→stage PRs must run CI (EV-036-D15 / TC-298)."""
    assert _CI_WORKFLOW.is_file()
    body = _CI_WORKFLOW.read_text(encoding="utf-8")
    assert "pull_request:" in body
    # stage must be a first-class PR/push target so integration PRs get CI.
    assert "stage" in body
    assert "branches:" in body
    # Guard: pull_request branches list includes stage (not only main/phase).
    pr_idx = body.index("pull_request:")
    pr_block = body[pr_idx : pr_idx + 200]
    assert "stage" in pr_block, "ci.yml pull_request.branches must include stage"


def test_deploy_staging_workflow_names_staging_smoke_check() -> None:
    """Ruleset contract: deploy-staging.yml must expose staging-smoke job name (TC-297)."""
    workflow = _REPO_ROOT / ".github" / "workflows" / "deploy-staging.yml"
    assert workflow.is_file()
    body = workflow.read_text(encoding="utf-8")
    assert "staging-smoke" in body
