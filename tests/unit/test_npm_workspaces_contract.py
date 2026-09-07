"""npm workspace helper contract guards.

[Corpus: feature-list.md §F62]
[Corpus: tests]
[Spec: docs/LOCAL_DEV.md]
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
NPM_WORKSPACES = REPO_ROOT / "scripts" / "npm_workspaces.sh"


def test_needs_npm_ci_checks_required_frontend_tools() -> None:
    """The helper should reinstall when any core frontend tool is missing."""
    text = NPM_WORKSPACES.read_text(encoding="utf-8")

    for marker in (
        "node_modules/.bin/eslint",
        "node_modules/.bin/tsc",
        "node_modules/.bin/prettier",
        "node_modules/.bin/vitest",
        "node_modules/.bin/vite",
    ):
        assert marker in text


def test_needs_npm_ci_checks_eslint_runtime_dependency() -> None:
    """The helper should detect the missing ESLint runtime dep seen in local verify-build."""
    text = NPM_WORKSPACES.read_text(encoding="utf-8")

    assert "node_modules/@eslint-community/eslint-utils/package.json" in text
