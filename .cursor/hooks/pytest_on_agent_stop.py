"""Cursor stop hook: run pytest when agent stops.

Follows hook contract: stdout is valid JSON, test output goes to stderr.
Always exits 0.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def find_repo_root() -> Path | None:
    cwd = Path.cwd()
    for candidate in [cwd, *cwd.parents]:
        if (candidate / "pyproject.toml").is_file() or (candidate / ".git").is_dir():
            return candidate
    return None


def main() -> int:
    try:
        json.load(sys.stdin)
    except json.JSONDecodeError:
        pass

    repo = find_repo_root()
    if repo is None:
        print("{}")
        return 0

    try:
        proc = subprocess.run(
            ["uv", "run", "pytest", "-q"],
            cwd=repo,
            capture_output=True,
            text=True,
            timeout=300,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        print("{}")
        return 0

    sys.stderr.write(proc.stdout)
    sys.stderr.write(proc.stderr)
    if proc.returncode != 0:
        sys.stderr.write(f"\n[pytest_on_agent_stop] exit {proc.returncode}\n")

    print("{}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
