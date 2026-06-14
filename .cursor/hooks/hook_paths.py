"""Shared path classification for Cursor afterFileEdit CI hooks."""

from __future__ import annotations

from pathlib import Path

SOURCE_ROOTS = frozenset({"apps", "packages", "tests"})
FRONTEND_APPS = frozenset({"chat-rag-frontend", "data-management-frontend"})
FRONTEND_PACKAGES = frozenset({"frontend-i18n", "frontend-ui"})
FORMATTABLE_SUFFIXES = frozenset(
    {
        ".py",
        ".pyi",
        ".ts",
        ".tsx",
        ".js",
        ".jsx",
        ".css",
        ".scss",
        ".json",
        ".md",
        ".html",
        ".yaml",
        ".yml",
    }
)
WORKSPACE_BY_DIR: dict[tuple[str, str], str] = {
    ("apps", "chat-rag-frontend"): "vecinita-chat-rag-frontend",
    ("apps", "data-management-frontend"): "vecinita-data-management-frontend",
    ("packages", "frontend-i18n"): "vecinita-frontend-i18n",
    ("packages", "frontend-ui"): "vecinita-frontend-ui",
}


def find_repo_root(start: Path) -> Path | None:
    p = start if start.is_dir() else start.parent
    for candidate in [p, *p.parents]:
        if (candidate / "pyproject.toml").is_file() or (candidate / ".git").is_dir():
            return candidate
    return None


def relative_parts(repo: Path, file_path: Path) -> tuple[str, ...] | None:
    try:
        return file_path.resolve().relative_to(repo.resolve()).parts
    except ValueError:
        return None


def format_lint_targets(repo: Path, file_path: Path) -> list[str]:
    """Make targets for Python edits only; frontend uses scoped npm via frontend_format_lint_workspace."""
    parts = relative_parts(repo, file_path)
    if not parts or parts[0] not in SOURCE_ROOTS:
        return []
    if file_path.suffix not in FORMATTABLE_SUFFIXES:
        return []

    if file_path.suffix in {".py", ".pyi"}:
        return ["format-py", "lint-fix-py"]

    return []


def frontend_format_lint_workspace(repo: Path, file_path: Path) -> str | None:
    """npm workspace for scoped Prettier/ESLint when a formattable frontend file is edited."""
    if file_path.suffix in {".py", ".pyi"} or file_path.suffix not in FORMATTABLE_SUFFIXES:
        return None
    parts = relative_parts(repo, file_path)
    if not parts or len(parts) < 2:
        return None
    return WORKSPACE_BY_DIR.get((parts[0], parts[1]))


def python_typecheck_target(repo: Path, file_path: Path) -> Path | None:
    if file_path.suffix != ".py":
        return None
    parts = relative_parts(repo, file_path)
    if not parts or parts[0] not in SOURCE_ROOTS:
        return None
    return file_path.resolve()


def frontend_typecheck_workspace(repo: Path, file_path: Path) -> str | None:
    if file_path.suffix not in {".ts", ".tsx", ".js", ".jsx"}:
        return None
    parts = relative_parts(repo, file_path)
    if not parts or len(parts) < 2:
        return None
    return WORKSPACE_BY_DIR.get((parts[0], parts[1]))
