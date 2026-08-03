"""TC-212-215 / UJ-068 / F63 - post-CD semver release tagging."""

from __future__ import annotations

from pathlib import Path

import pytest
from scripts.ci.release_semver import (
    next_patch_tag,
    should_skip_release,
    strict_semver_tags,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
RELEASE_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "release.yml"


@pytest.mark.unit
def test_next_patch_from_strict_semver_only() -> None:
    """TC-212 / AC-REL2 / S025-D11."""
    tags = [
        "v0.2.0-deploy",
        "v0.4.0",
        "v1.0-stable-verified",
        "v0.3.9",
    ]
    assert strict_semver_tags(tags) == ["v0.3.9", "v0.4.0"]
    assert next_patch_tag(tags) == "v0.4.1"
    assert next_patch_tag(["v0.3.0"]) == "v0.3.1"
    assert next_patch_tag([]) == "v0.1.0"


@pytest.mark.unit
def test_skip_release_on_marker_in_commit_message() -> None:
    """TC-213 / AC-REL4."""
    assert should_skip_release("chore: docs [skip release]") is True
    assert should_skip_release("feat: ship hooks") is False


@pytest.mark.unit
def test_idempotent_when_head_already_tagged() -> None:
    """TC-214 / AC-REL4."""
    assert should_skip_release("feat: x", head_tags=["v0.4.1"]) is True
    assert should_skip_release("feat: x", head_tags=[]) is False


@pytest.mark.unit
def test_release_workflow_triggers_after_deploy_digitalocean() -> None:
    """TC-215 / AC-REL1 / AC-REL3 / S025-D12."""
    assert RELEASE_WORKFLOW.is_file(), "release.yml must exist"
    text = RELEASE_WORKFLOW.read_text(encoding="utf-8")
    assert 'workflows: ["Deploy DigitalOcean"]' in text
    assert "types: [completed]" in text
    assert "contents: write" in text
    assert "gh release create" in text
    # Annotated tag on Actions requires committer identity (S025 13-deploy-smoke).
    assert 'user.email "41898282+github-actions[bot]@users.noreply.github.com"' in text
    assert "git tag -a" in text
