"""Cursor stop hook: fast checks when the agent session ends.

Runs `make check-fast` (lint + typecheck) and `make test-fast` (scoped unit tests)
when source files have local changes. Pre-push runs the same fast tier; run `make ci-push`
before opening a PR. Advisory only — always exits 0.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

OUTPUT_TAIL_CHARS = 4000


def find_repo_root() -> Path | None:
    cwd = Path.cwd()
    for candidate in [cwd, *cwd.parents]:
        if (candidate / "pyproject.toml").is_file() or (candidate / ".git").is_dir():
            return candidate
    return None


def _run_make(repo: Path, target: str, timeout: int) -> subprocess.CompletedProcess[str] | None:
    try:
        return subprocess.run(
            ["make", target],
            cwd=repo,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        sys.stderr.write(f"[check_fast_on_stop] could not run make {target}: {exc}\n")
        return None


def _log_result(label: str, proc: subprocess.CompletedProcess[str] | None) -> None:
    if proc is None:
        return
    sys.stderr.write(proc.stdout)
    sys.stderr.write(proc.stderr)
    if proc.returncode != 0:
        combined = proc.stdout + proc.stderr
        tail = combined[-OUTPUT_TAIL_CHARS:] if len(combined) > OUTPUT_TAIL_CHARS else combined
        sys.stderr.write(
            f"\n[check_fast_on_stop] {label} exit {proc.returncode} "
            "(advisory — full CI runs on git push via husky)\n"
        )
        sys.stderr.write(tail.strip())
        sys.stderr.write("\n")
    else:
        sys.stderr.write(f"\n[check_fast_on_stop] {label} passed\n")


def main() -> int:
    try:
        json.load(sys.stdin)
    except json.JSONDecodeError:
        pass

    repo = find_repo_root()
    if repo is None:
        print("{}")
        return 0

    check_proc = _run_make(repo, "check-fast", timeout=600)
    _log_result("check-fast", check_proc)

    test_proc = _run_make(repo, "test-fast", timeout=900)
    _log_result("test-fast", test_proc)

    print("{}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
