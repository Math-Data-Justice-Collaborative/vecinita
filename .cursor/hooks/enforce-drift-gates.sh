#!/usr/bin/env bash
# Cursor beforeShellExecution hook:
# - Intercepts `git commit ...` and `gh pr create ...`
# - Enforces drift gates before the shell command is allowed:
#   1) OpenAPI client sync check when schema/client surfaces are touched
#   2) Lint/type checks for touched services only
# - Returns JSON permission response with actionable remediation.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

emit_allow() {
  printf '%s\n' '{ "permission": "allow" }'
}

emit_deny() {
  local msg="$1"
  python3 - "$msg" <<'PY'
import json
import sys
print(json.dumps({"permission": "deny", "user_message": sys.argv[1]}))
PY
}

if ! command -v python3 >/dev/null 2>&1; then
  emit_deny "Drift enforcement hook requires python3, but python3 is not available on PATH."
  exit 0
fi

INPUT="$(cat || true)"

readarray -t PARSED < <(
  python3 - "$INPUT" <<'PY'
import json
import sys

raw = sys.argv[1]
try:
    payload = json.loads(raw) if raw.strip() else {}
except json.JSONDecodeError:
    print("")
    print("0")
    raise SystemExit(0)

cmd = str(payload.get("command") or "").strip()
is_target = int(cmd.startswith("git commit") or cmd.startswith("gh pr create"))
print(cmd)
print(is_target)
PY
)

COMMAND="${PARSED[0]:-}"
IS_TARGET="${PARSED[1]:-0}"

if [[ "$IS_TARGET" != "1" ]]; then
  emit_allow
  exit 0
fi

if ! command -v git >/dev/null 2>&1; then
  emit_deny "Drift enforcement hook requires git, but git is not available on PATH."
  exit 0
fi

readarray -t CHECKS < <(
  python3 - "$ROOT" <<'PY'
import os
import subprocess
import sys

root = sys.argv[1]

def changed_paths(repo: str) -> list[str]:
    cmds = [
        ["git", "-C", repo, "diff", "--name-only", "--diff-filter=ACMRT", "HEAD"],
        ["git", "-C", repo, "ls-files", "--others", "--exclude-standard"],
    ]
    out: list[str] = []
    for cmd in cmds:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=120, check=False)
        if r.returncode != 0:
            raise RuntimeError(f"failed command: {' '.join(cmd)}")
        out.extend(line.strip() for line in r.stdout.splitlines() if line.strip())
    return sorted(set(out))

paths = changed_paths(root)
path_set = set(paths)

def touched(prefix: str) -> bool:
    return any(p == prefix or p.startswith(prefix + "/") for p in path_set)

checks: list[str] = []

schema_markers = (
    "apis/gateway/openapi.json",
    "backend/openapi.json",
    "apis/gateway/src/api",
    "backend/src/api",
    "backend/src/routes",
    "backend/src/models",
    "packages/openapi-clients",
    "scripts/openapi_codegen.sh",
    "apis/data-management-api/apps/backend",
    "apis/data-management-api/packages/service-clients",
)
if any(touched(marker) for marker in schema_markers):
    checks.append("openapi-codegen-verify")

if touched("apis/gateway") or touched("apis/agent") or touched("backend"):
    checks.extend(["lint-backend", "typecheck-backend"])
if touched("frontends/chat"):
    checks.extend(["lint-frontend", "typecheck-frontend"])
if touched("frontends/data-management"):
    checks.append("lint-data-management-frontend")
if touched("modal-apps/scraper"):
    checks.extend(["lint-scraper", "typecheck-scraper"])
if touched("modal-apps/embedding-modal"):
    checks.append("lint-embedding-modal")
if touched("modal-apps/model-modal"):
    checks.append("lint-model-modal")

for check in checks:
    print(check)
PY
)

if [[ "${#CHECKS[@]}" -eq 0 ]]; then
  emit_allow
  exit 0
fi

LOG="$(mktemp)"
trap 'rm -f "$LOG"' EXIT

FAILED_TARGET=""
for target in "${CHECKS[@]}"; do
  echo "[cursor hook] Running make ${target}" >&2
  set +e
  make "${target}" >>"$LOG" 2>&1
  rc=$?
  set -e
  if [[ "$rc" -ne 0 ]]; then
    FAILED_TARGET="${target}"
    break
  fi
done

if [[ -z "$FAILED_TARGET" ]]; then
  emit_allow
  exit 0
fi

TAIL="$(python3 - "$LOG" <<'PY'
from pathlib import Path
import sys
raw = Path(sys.argv[1]).read_text(errors="replace")
print(raw[-8000:] if len(raw) > 8000 else raw)
PY
)"

REMEDIATION=$(
  python3 - "$FAILED_TARGET" "$COMMAND" "$TAIL" <<'PY'
import sys
failed_target, command, tail = sys.argv[1], sys.argv[2], sys.argv[3]
print(
    "Blocked by drift enforcement before running: "
    f"`{command}`.\n\n"
    f"Failed check: `make {failed_target}`.\n\n"
    "Remediation:\n"
    "1) Run the failing target locally and fix issues.\n"
    "2) If API schema/contracts changed, run `make openapi-codegen-verify` and commit generated client updates.\n"
    "3) Re-run this command once checks pass.\n\n"
    "Last output:\n"
    f"{tail}"
)
PY
)

emit_deny "$REMEDIATION"
exit 0
