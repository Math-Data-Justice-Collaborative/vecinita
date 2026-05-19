"""Cursor preToolUse hook: advisory reminder to verify spec source before writing.

Reads the active task from execution-plan.md §Current State and returns a
reminder about the spec source. Advisory only — never blocks.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


def find_repo_root(start: Path) -> Path | None:
    p = start if start.is_dir() else start.parent
    for candidate in [p, *p.parents]:
        if (candidate / "pyproject.toml").is_file() or (candidate / ".git").is_dir():
            return candidate
    return None


def read_active_task(repo: Path) -> str | None:
    plan = repo / "docs" / "execution-plan.md"
    if not plan.is_file():
        return None
    try:
        text = plan.read_text(encoding="utf-8")
    except OSError:
        return None

    match = re.search(
        r"\|\s*\*\*Active task\*\*\s*\|\s*(\S+)\s*\|", text
    )
    if not match:
        return None

    task_id = match.group(1)
    task_pattern = re.compile(
        rf"\|\s*{re.escape(task_id)}\s*\|(.+?)(?=\n\||\n\n|\Z)",
        re.DOTALL,
    )
    task_match = task_pattern.search(text)
    if not task_match:
        return task_id

    row = task_match.group(0)
    cells = [c.strip() for c in row.split("|") if c.strip()]
    if len(cells) >= 5:
        return f"{task_id} — Spec Source: {cells[4]}"
    return task_id


def is_source_file(repo: Path, file_path: Path) -> bool:
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
    if repo is None or not is_source_file(repo, file_path):
        print("{}")
        return 0

    active = read_active_task(repo)
    if active:
        result = {
            "additional_context": (
                f"[pre-task-check] Active task: {active}. "
                "Verify spec source has been read before implementing."
            )
        }
    else:
        result = {}

    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
