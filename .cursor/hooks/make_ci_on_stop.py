"""Cursor stop hook: run full CI parity (`make ci`) when the agent session ends.

Make serializes npm via scripts/npm_with_lock.sh; do not hold the same flock here
(deadlock). Test output goes to stderr. On failure, returns followup_message. Always exits 0.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

OUTPUT_TAIL_CHARS = 8000


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

    # Do not hold repo_make_lock here: make ci uses scripts/npm_with_lock.sh on the
    # same flock file and would deadlock until the hook subprocess is killed (SIGTERM).
    try:
        proc = subprocess.run(
            ["make", "ci"],
            cwd=repo,
            capture_output=True,
            text=True,
            timeout=3600,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        sys.stderr.write(f"[make_ci_on_stop] could not run make ci: {exc}\n")
        print("{}")
        return 0

    sys.stderr.write(proc.stdout)
    sys.stderr.write(proc.stderr)

    if proc.returncode != 0:
        combined = proc.stdout + proc.stderr
        tail = combined[-OUTPUT_TAIL_CHARS:] if len(combined) > OUTPUT_TAIL_CHARS else combined
        sys.stderr.write(f"\n[make_ci_on_stop] exit {proc.returncode}\n")
        result = {
            "followup_message": (
                f"[make ci] failed (exit {proc.returncode}). "
                "Fix the failures below before ending the session:\n\n"
                + tail.strip()
            )
        }
    else:
        sys.stderr.write("\n[make_ci_on_stop] make ci passed\n")
        result = {}

    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
