"""Cursor afterFileEdit hook: auto-fix formatting and lint via Make targets.

Python: `make format-py lint-fix-py`.
Frontend apps/packages: scoped Prettier + ESLint --fix for the edited workspace.
Skips when CI holds the shared repo lock to avoid npm ci corruption. Always exits 0.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from hook_paths import (
    find_repo_root,
    format_lint_targets,
    frontend_format_lint_workspace,
)
from repo_make_lock import repo_lock


def run_frontend_format_lint(
    repo: Path, workspace: str
) -> subprocess.CompletedProcess[str] | None:
    shell_cmd = (
        "bash scripts/npm_workspaces.sh install && "
        f"bash scripts/npm_workspaces.sh run format {workspace} && "
        f"npm exec -w {workspace} -- eslint src --fix"
    )
    cmd = ["bash", "scripts/npm_with_lock.sh", "bash", "-eu", "-o", "pipefail", "-c", shell_cmd]
    try:
        return subprocess.run(
            cmd,
            cwd=repo,
            capture_output=True,
            text=True,
            timeout=300,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None


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

    targets = format_lint_targets(repo, file_path)
    workspace = frontend_format_lint_workspace(repo, file_path)

    if not targets and workspace is None:
        print("{}")
        return 0

    with repo_lock(repo, "make-hooks", exclusive=True, blocking=False) as acquired:
        if not acquired:
            print("{}")
            return 0

        outputs: list[str] = []
        failed = False

        if targets:
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
                failed = True
                outputs.append(proc.stdout)
                outputs.append(proc.stderr)

        if workspace is not None:
            proc = run_frontend_format_lint(repo, workspace)
            if proc is None:
                print("{}")
                return 0
            if proc.returncode != 0:
                failed = True
                outputs.append(proc.stdout)
                outputs.append(proc.stderr)

    if failed:
        output = "\n".join(part.strip() for part in outputs if part and part.strip())
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
