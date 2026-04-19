#!/usr/bin/env bash
# Cursor `stop` hook (https://cursor.com/docs/agent/third-party-hooks):
# When the agent loop ends with status "completed", run `make ci` (local CI gate)
# only if the turn touched at least one non-prose file (e.g. .py, .tsx). Edits
# limited to documentation-style extensions (.md, .txt, …) skip the gate.
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
# run_make_ci: 1 = run gate, 0 = skip (docs-only / no paths), empty = not completed or parse error
RUN_MAKE_CI=$(
	python3 - "$INPUT" "$ROOT" <<'PY'
import json
import subprocess
import sys

raw, root = sys.argv[1], sys.argv[2]

try:
    payload = json.loads(raw) if raw.strip() else {}
except json.JSONDecodeError:
    print("", end="")
    raise SystemExit(0)

if payload.get("status") != "completed":
    print("", end="")
    raise SystemExit(0)

# Prose / plain-text doc extensions only — everything else is treated as code/config/assets.
TEXT_DOC_EXT = frozenset({".md", ".markdown", ".txt", ".rst", ".adoc", ".asciidoc"})


def file_ext(path: str) -> str:
    p = path.lower().replace("\\", "/")
    slash = p.rfind("/")
    base = p[slash + 1 :]
    dot = base.rfind(".")
    return base[dot:] if dot != -1 else ""


def git_changed_paths(repo: str) -> list[str] | None:
    """Paths changed vs HEAD (tracked + untracked). None if git is unavailable."""
    try:
        r = subprocess.run(
            ["git", "-C", repo, "rev-parse", "--is-inside-work-tree"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if r.returncode != 0 or r.stdout.strip() != "true":
            return None
    except (OSError, subprocess.TimeoutExpired):
        return None

    paths: list[str] = []
    for cmd in (
        ["git", "-C", repo, "diff", "--name-only", "--diff-filter=ACMRT", "HEAD"],
        ["git", "-C", repo, "ls-files", "--others", "--exclude-standard"],
    ):
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if r.returncode != 0:
                return None
            paths.extend(line.strip() for line in r.stdout.splitlines() if line.strip())
        except (OSError, subprocess.TimeoutExpired):
            return None
    return paths


def should_run_make_ci(repo: str, hook: dict) -> bool:
    modified = hook.get("modified_files")
    if isinstance(modified, list) and modified:
        paths = [str(p).strip() for p in modified if str(p).strip()]
    else:
        paths = git_changed_paths(repo)
        if paths is None:
            return True

    if not paths:
        return False

    return any(file_ext(p) not in TEXT_DOC_EXT for p in paths)


print("1" if should_run_make_ci(root, payload) else "0", end="")
PY
) || RUN_MAKE_CI=""

if [[ "$RUN_MAKE_CI" == "0" ]]; then
	echo "[cursor hook] Skipping make ci (only prose/text doc extensions touched, or no changed paths vs HEAD)." >&2
	emit '{}'
	exit 0
fi

# Unknown / empty after completed: treat as run (e.g. JSON parse failure, or python crashed).
if [[ "$RUN_MAKE_CI" != "1" ]]; then
	echo "[cursor hook] Could not classify changed files — running make ci." >&2
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
