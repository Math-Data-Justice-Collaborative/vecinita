#!/usr/bin/env bash
# Serialize frontend npm operations (make ci, hooks) to avoid node_modules corruption.
set -eo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
bash "${ROOT}/scripts/ensure_node24.sh"
DIGEST="$(printf '%s' "$ROOT" | sha256sum | awk '{print substr($1,1,16)}')"
LOCK="/tmp/vecinita-make-hooks-${DIGEST}.lock"

# Prefer util-linux flock when present; otherwise run unlocked (common on macOS).
run_locked() {
  if command -v flock >/dev/null 2>&1; then
    flock -w 600 "$LOCK" "$@"
  else
    "$@"
  fi
}

if [[ "${1:-}" == "bash" ]]; then
  shift
  run_locked bash --noprofile --norc "$@"
  exit $?
fi

run_locked "$@"
