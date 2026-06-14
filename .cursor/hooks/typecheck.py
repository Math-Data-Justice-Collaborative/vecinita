"""Cursor afterFileEdit hook: report type errors after auto-fix hooks run.

Python: basedpyright on the edited file under apps/, packages/, or tests/.
Frontend: scoped `npm run typecheck` for the edited workspace.
Always exits 0; failures go to additional_context.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from hook_paths import (
    find_repo_root,
    frontend_typecheck_workspace,
    python_typecheck_target,
)
from repo_make_lock import repo_lock


def run_python_typecheck(repo: Path, target: Path) -> subprocess.CompletedProcess[str] | None:
    try:
        return subprocess.run(
            ["uv", "run", "basedpyright", str(target)],
            cwd=repo,
            capture_output=True,
            text=True,
            timeout=120,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None


def run_frontend_typecheck(repo: Path, workspace: str) -> subprocess.CompletedProcess[str] | None:
    cmd = [
        "bash",
        "scripts/npm_with_lock.sh",
        "bash",
        "scripts/npm_workspaces.sh",
        "run",
        "typecheck",
        workspace,
    ]
    try:
        with repo_lock(repo, "make-hooks", exclusive=True, blocking=False) as acquired:
            if not acquired:
                return None
            return subprocess.run(
                cmd,
                cwd=repo,
                capture_output=True,
                text=True,
                timeout=300,
            )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None


def summarize_pyright(proc: subprocess.CompletedProcess[str]) -> str | None:
    if proc.returncode == 0:
        return None
    lines = proc.stdout.strip().splitlines()
    error_lines = [line for line in lines if "error:" in line.lower()]
    if error_lines:
        return "\n".join(error_lines[:20])
    output = "\n".join(part.strip() for part in (proc.stdout, proc.stderr) if part.strip())
    return output or None


def summarize_tsc(proc: subprocess.CompletedProcess[str]) -> str | None:
    if proc.returncode == 0:
        return None
    output = "\n".join(part.strip() for part in (proc.stdout, proc.stderr) if part.strip())
    return output or None


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

    messages: list[str] = []

    py_target = python_typecheck_target(repo, file_path)
    if py_target is not None:
        proc = run_python_typecheck(repo, py_target)
        if proc is not None:
            summary = summarize_pyright(proc)
            if summary:
                messages.append(f"[basedpyright] Type errors:\n{summary}")

    workspace = frontend_typecheck_workspace(repo, file_path)
    if workspace is not None:
        proc = run_frontend_typecheck(repo, workspace)
        if proc is not None:
            summary = summarize_tsc(proc)
            if summary:
                messages.append(f"[tsc] Type errors in {workspace}:\n{summary}")

    result = {"additional_context": "\n\n".join(messages)} if messages else {}

    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
