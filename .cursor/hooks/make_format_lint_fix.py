"""Cursor afterFileEdit hook: auto-fix formatting and lint via Make targets.

Runs scoped `make format-* lint-fix-*` targets when a formattable source file is edited.
Skips when CI holds the shared repo lock to avoid npm ci corruption. Always exits 0.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from repo_make_lock import repo_lock

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
SOURCE_ROOTS = frozenset({"apps", "packages", "tests"})
FRONTENDS = frozenset({"chat-rag-frontend", "data-management-frontend"})


def find_repo_root(start: Path) -> Path | None:
    p = start if start.is_dir() else start.parent
    for candidate in [p, *p.parents]:
        if (candidate / "pyproject.toml").is_file() or (candidate / ".git").is_dir():
            return candidate
    return None


def make_targets(repo: Path, file_path: Path) -> list[str]:
    try:
        rel = file_path.resolve().relative_to(repo.resolve())
    except ValueError:
        return []

    parts = rel.parts
    if not parts or parts[0] not in SOURCE_ROOTS:
        return []
    if file_path.suffix not in FORMATTABLE_SUFFIXES:
        return []

    if file_path.suffix in {".py", ".pyi"} and parts[0] in {"apps", "packages", "tests"}:
        return ["format-py", "lint-fix-py"]

    if len(parts) >= 2 and parts[0] == "apps" and parts[1] in FRONTENDS:
        return ["format-fe", "lint-fix-fe"]

    return []


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        print("{}")
        return 0

    raw = payload.get("filePath") or payload.get("file_path") or ""
    if not raw:
        print("{}")
        return 0

    file_path = Path(raw)
    repo = find_repo_root(file_path)
    if repo is None:
        print("{}")
        return 0

    targets = make_targets(repo, file_path)
    if not targets:
        print("{}")
        return 0

    with repo_lock(repo, "make-hooks", exclusive=True, blocking=False) as acquired:
        if not acquired:
            print("{}")
            return 0

        try:
            proc = subprocess.run(
                ["make", *targets],
                cwd=repo,
                capture_output=True,
                text=True,
                timeout=300,
            )
        except (FileNotFoundError, subprocess.TimeoutExpired):
            print("{}")
            return 0

    if proc.returncode != 0:
        output = "\n".join(part.strip() for part in (proc.stdout, proc.stderr) if part.strip())
        result = {
            "additional_context": (
                "[make format/lint-fix] Auto-fix failed. Remaining issues:\n" + output
            )
        }
    else:
        result = {}

    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
