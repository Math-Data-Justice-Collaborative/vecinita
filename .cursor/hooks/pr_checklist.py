"""Cursor preToolUse hook: advisory PR checklist before git push / gh pr.

Fires on Shell tool use. If the command contains 'git push' or 'gh pr',
returns a reminder about the PR checklist. Advisory only.
"""

from __future__ import annotations

import json
import sys

PR_CHECKLIST = """\
PR Checklist (from execution-plan.md §Git Strategy):
  - [ ] All milestone tasks completed in execution plan
  - [ ] ruff lint passes on all changed files
  - [ ] ruff format passes on all changed files
  - [ ] pyright passes (no errors)
  - [ ] Full test suite passes (pytest -v)
  - [ ] No WIP commits in the branch
  - [ ] Commit messages follow [T{id}] format
  - [ ] PR title matches convention ([M{n}] name or Phase {n}: name)
  - [ ] execution-plan.md task statuses updated"""

GIT_PUSH_TRIGGERS = ("git push", "gh pr create", "gh pr ")


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        print("{}")
        return 0

    command = payload.get("command") or payload.get("input") or ""
    if not command:
        print("{}")
        return 0

    if any(trigger in command for trigger in GIT_PUSH_TRIGGERS):
        result = {"additional_context": f"[pr-checklist] {PR_CHECKLIST}"}
    else:
        result = {}

    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
