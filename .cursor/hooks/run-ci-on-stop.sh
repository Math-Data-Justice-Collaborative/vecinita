#!/usr/bin/env bash
# Cursor `stop` hook (https://cursor.com/docs/agent/third-party-hooks):
# When the agent loop ends with status "completed", run `make ci` (local CI gate).
# If it fails, stdout returns JSON with `followup_message` so Cursor submits a
# follow-up and the task is not treated as done until CI passes.
#
# Disable: SKIP_CI_HOOK=1

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

emit() {
	printf '%s\n' "$1"
}

if [[ "${SKIP_CI_HOOK:-}" == "1" ]]; then
	echo "[cursor hook] SKIP_CI_HOOK=1 — skipping make ci" >&2
	emit '{}'
	exit 0
fi

if ! command -v python3 >/dev/null 2>&1; then
	echo "[cursor hook] python3 missing — cannot run CI gate; allow stop" >&2
	emit '{}'
	exit 0
fi

INPUT=$(cat || true)
STATUS=$(python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('status',''))" <<<"$INPUT" 2>/dev/null || echo "")

if [[ "$STATUS" != "completed" ]]; then
	emit '{}'
	exit 0
fi

if ! command -v make >/dev/null 2>&1; then
	echo "[cursor hook] make missing — cannot run CI gate; allow stop" >&2
	emit '{}'
	exit 0
fi

LOG="$(mktemp)"
trap 'rm -f "$LOG"' EXIT

echo "[cursor hook] Running make ci before completing (repo: ${ROOT})…" >&2
set +e
make ci >"$LOG" 2>&1
RC=$?
set -e
if [[ "$RC" -eq 0 ]]; then
	echo "[cursor hook] make ci passed." >&2
else
	echo "[cursor hook] make ci failed (exit ${RC}); injecting follow-up message." >&2
fi

python3 - "$LOG" "$RC" <<'PY'
import json
import sys

path, rc_s = sys.argv[1], sys.argv[2]
try:
    rc = int(rc_s)
except ValueError:
    rc = 1

with open(path, errors="replace") as f:
    raw = f.read()

tail = raw[-12000:] if len(raw) > 12000 else raw

if rc == 0:
    print("{}")
else:
    msg = (
        "The local CI gate (`make ci`) failed — do not treat this task as complete until it passes.\n\n"
        "Fix the errors below, run `make ci` again from the repo root until it exits 0, then summarize what changed.\n\n"
        f"```\n{tail}\n```"
    )
    print(json.dumps({"followup_message": msg}))
PY

exit 0
