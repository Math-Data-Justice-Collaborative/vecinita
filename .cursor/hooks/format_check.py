"""Cursor afterFileEdit hook: run Ruff format check on edited Python files.

Returns formatting diff in additional_context if changes needed.
Always exits 0.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def find_repo_root(start: Path) -> Path | None:
    p = start if start.is_dir() else start.parent
    for candidate in [p, *p.parents]:
        if (candidate / "pyproject.toml").is_file() or (candidate / ".git").is_dir():
            return candidate
    return None


def should_check(repo: Path, file_path: Path) -> bool:
    if file_path.suffix != ".py":
        return False
    try:
        rel = file_path.resolve().relative_to(repo.resolve())
    except ValueError:
        return False
    parts = rel.parts
    if not parts:
        return False
    return parts[0] in ("src", "tests")


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
    if repo is None or not should_check(repo, file_path):
        print("{}")
        return 0

    try:
        proc = subprocess.run(
            ["uv", "run", "ruff", "format", "--check", "--diff", str(file_path.resolve())],
            cwd=repo,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        print("{}")
        return 0

    if proc.returncode != 0 and proc.stdout.strip():
        result = {
            "additional_context": (
                f"[ruff-format] File needs formatting:\n{proc.stdout.strip()}"
            )
        }
    else:
        result = {}

    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
