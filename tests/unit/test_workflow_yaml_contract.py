"""Workflow YAML contract guards for deploy pipelines.

[Corpus: deploy-integration] [Corpus: staging] [Corpus: tests]
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DEPLOY_WORKFLOWS = (
    REPO_ROOT / ".github/workflows/deploy-modal.yml",
    REPO_ROOT / ".github/workflows/deploy-digitalocean.yml",
)
CI_WORKFLOW = REPO_ROOT / ".github/workflows/ci.yml"
SETUP_NODE_V4_SHA = "49933ea5288caeca8642d1e84afbd3f7d6820020"
SETUP_NODE_V6_2_0_SHA = "6044e13b5dc448c55e2357c09f80417699197238"
HF_HUB_DISABLE_XET_LINE = 'HF_HUB_DISABLE_XET: "1"'


def _env_block_duplicate_keys(text: str) -> set[str]:
    duplicates: set[str] = set()
    lines = text.splitlines()
    index = 0
    while index < len(lines):
        line = lines[index]
        stripped = line.strip()
        if stripped != "env:":
            index += 1
            continue

        env_indent = len(line) - len(line.lstrip(" "))
        seen: set[str] = set()
        index += 1
        while index < len(lines):
            current = lines[index]
            current_stripped = current.strip()
            current_indent = len(current) - len(current.lstrip(" "))
            if current_stripped and current_indent <= env_indent:
                break
            if not current_stripped or current_stripped.startswith("#"):
                index += 1
                continue
            if current_indent == env_indent + 2 and ":" in current_stripped:
                key = current_stripped.split(":", maxsplit=1)[0].strip()
                if key in seen:
                    duplicates.add(key)
                seen.add(key)
            index += 1
    return duplicates


def test_deploy_workflows_have_no_duplicate_yaml_keys() -> None:
    """Deploy workflows must not redefine the same mapping key in one block."""
    for workflow_path in DEPLOY_WORKFLOWS:
        duplicates = _env_block_duplicate_keys(workflow_path.read_text(encoding="utf-8"))
        assert not duplicates, f"{workflow_path.name} has duplicate env keys: {sorted(duplicates)}"


def test_ci_workflow_uses_setup_node_pin_without_known_node24_deprecation_regression() -> None:
    """CI should avoid the older setup-node pin that emits Node 24 deprecation spam."""
    text = CI_WORKFLOW.read_text(encoding="utf-8")
    assert SETUP_NODE_V4_SHA not in text
    assert SETUP_NODE_V6_2_0_SHA in text


def test_ci_workflow_disables_hf_xet_to_avoid_known_upstream_warning() -> None:
    """CI should disable Xet so pytest does not surface the upstream hf_xet deprecation."""
    text = CI_WORKFLOW.read_text(encoding="utf-8")
    assert HF_HUB_DISABLE_XET_LINE in text
