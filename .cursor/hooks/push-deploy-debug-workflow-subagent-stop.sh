#!/usr/bin/env bash
# Cursor `subagentStop` hook: after push-deploy-debug-workflow Task completes, nudge
# the parent if the summary omits GitHub CI completion and/or (after CI green) Render
# completion markers. Does not run long polls (see agent Phase D / F).
#
# Input: JSON on stdin. Output: JSON on stdout.

set -euo pipefail

exec python3 -c '
import json
import sys

raw = sys.stdin.read() or "{}"
try:
    d = json.loads(raw)
except json.JSONDecodeError:
    print("{}")
    raise SystemExit(0)

if d.get("subagent_type") != "push-deploy-debug-workflow":
    print("{}")
    raise SystemExit(0)

if d.get("status") != "completed":
    print("{}")
    raise SystemExit(0)

try:
    loop_count = int(d.get("loop_count") or 0)
except (TypeError, ValueError):
    loop_count = 0

if loop_count >= 3:
    print("{}")
    raise SystemExit(0)

summary = (d.get("summary") or "").lower()

no_push = any(
    m in summary
    for m in (
        "no push-triggered ci watch",
        "no push executed",
        "no pushes performed",
        "review-only stop",
    )
)

ci_done = any(
    m in summary
    for m in (
        "## ci error summary",
        "all workflow runs for this commit succeeded",
    )
)

render_done = any(
    m in summary
    for m in (
        "## render deploy summary",
        "## render failure summary",
        "render deploy skipped",
    )
)

if no_push:
    print("{}")
    raise SystemExit(0)

if not ci_done:
    msg = (
        "The **push-deploy-debug-workflow** subagent finished without a clear **GitHub Actions** "
        "completion block (no `## CI error summary`, no explicit all-green line, and no clear no-push note). "
        "If **Phase C** did a **root** `git push`, complete **Phase D** now: follow "
        "`.cursor/skills/github-actions-poll-until-complete/SKILL.md`, update ledger **CI watch**, "
        "and emit **`## CI error summary`** or state that all runs succeeded."
    )
    print(json.dumps({"followup_message": msg}))
    raise SystemExit(0)

if ("all workflow runs for this commit succeeded" in summary) and (not render_done):
    msg = (
        "GitHub Actions look **all green** in the summary, but there is no **`## Render deploy summary`**, "
        "**`## Render failure summary`**, or **Render deploy skipped** line. If Phase **E** is satisfied, "
        "run **Phase F** now: Render MCP `list_services` / `list_deploys` / `get_deploy` until terminal, "
        "then summarize with **`## Render deploy summary`** or **`## Render failure summary`** and debug "
        "any failures per the agent instructions."
    )
    print(json.dumps({"followup_message": msg}))
    raise SystemExit(0)

print("{}")
'
