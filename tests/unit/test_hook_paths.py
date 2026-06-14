"""Path classification for Cursor afterFileEdit CI hooks."""

from __future__ import annotations

import sys
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parents[2] / ".cursor" / "hooks"
sys.path.insert(0, str(HOOKS_DIR))

from hook_paths import (  # noqa: E402
    format_lint_targets,
    frontend_format_lint_workspace,
    frontend_typecheck_workspace,
)


def _repo() -> Path:
    return Path(__file__).resolve().parents[2]


def test_format_lint_targets_python_file() -> None:
    repo = _repo()
    target = repo / "packages/rag/vecinita_rag/engine.py"
    assert format_lint_targets(repo, target) == ["format-py", "lint-fix-py"]


def test_format_lint_targets_frontend_package_ts() -> None:
    repo = _repo()
    target = repo / "packages/frontend-ui/src/index.ts"
    assert format_lint_targets(repo, target) == []


def test_frontend_format_lint_workspace_package() -> None:
    repo = _repo()
    target = repo / "packages/frontend-i18n/src/t.ts"
    assert frontend_format_lint_workspace(repo, target) == "vecinita-frontend-i18n"


def test_frontend_format_lint_workspace_app() -> None:
    repo = _repo()
    target = repo / "apps/chat-rag-frontend/src/App.tsx"
    assert frontend_format_lint_workspace(repo, target) == "vecinita-chat-rag-frontend"


def test_frontend_format_lint_workspace_ignores_python() -> None:
    repo = _repo()
    target = repo / "packages/frontend-ui/not-real.py"
    assert frontend_format_lint_workspace(repo, target) is None


def test_frontend_typecheck_workspace_matches_format_lint_for_ts() -> None:
    repo = _repo()
    target = repo / "packages/frontend-ui/src/index.ts"
    assert frontend_typecheck_workspace(repo, target) == frontend_format_lint_workspace(
        repo, target
    )
