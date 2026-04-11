#!/usr/bin/env bash
# Cursor `stop` hook (https://cursor.com/docs/agent/third-party-hooks):
# When the agent loop ends with status "completed", run `make ci` (local CI gate).
# If `make ci` fails, run `make format` and `make lint-fix`, then `make ci` again.
# If it still fails, stdout returns JSON with `followup_message` for a follow-up turn.
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

if [[ "$RC" -ne 0 ]]; then
	echo "[cursor hook] make ci failed (exit ${RC}); running make format && make lint-fix && make ci (stop on first error)…" >&2
	set +e
	{
		echo ""
		echo "=== [cursor hook] make format (auto) ==="
		make format && \
		echo "" && echo "=== [cursor hook] make lint-fix (auto) ===" && \
		make lint-fix && \
		echo "" && echo "=== [cursor hook] make ci (retry after format/lint-fix) ===" && \
		make ci
	} >>"$LOG" 2>&1
	RC=$?
	set -e
	if [[ "$RC" -eq 0 ]]; then
		echo "[cursor hook] make ci passed after format/lint-fix." >&2
	else
		echo "[cursor hook] make ci still failing (exit ${RC}); injecting follow-up message." >&2
	fi
else
	echo "[cursor hook] make ci passed." >&2
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
        "The local CI gate (`make ci`) failed after automatically running `make format` and "
        "`make lint-fix` and retrying `make ci`. Address any remaining issues below, run "
        "`make ci` until it exits 0, then summarize what changed.\n\n"
        f"```\n{tail}\n```"
    )
    print(json.dumps({"followup_message": msg}))
PY

exit 0
