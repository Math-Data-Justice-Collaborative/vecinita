#!/usr/bin/env bash
# Serialize frontend npm operations (make ci, hooks) to avoid node_modules corruption.
set -eo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
bash "${ROOT}/scripts/ensure_node24.sh"
DIGEST="$(printf '%s' "$ROOT" | sha256sum | awk '{print substr($1,1,16)}')"
LOCK="/tmp/vecinita-make-hooks-${DIGEST}.lock"

if [[ "${1:-}" == "bash" ]]; then
  shift
  exec flock -w 600 "$LOCK" bash --noprofile --norc "$@"
fi

exec flock -w 600 "$LOCK" "$@"
