#!/usr/bin/env bash
# CI guard: hooks.json must bootstrap with python3, not uv run python (EV-029 deadlock fix).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HOOKS_JSON="${ROOT}/.cursor/hooks.json"

if [[ ! -f "${HOOKS_JSON}" ]]; then
  echo "ERROR: missing ${HOOKS_JSON}" >&2
  exit 1
fi

if rg -q 'uv run python .cursor/hooks' "${HOOKS_JSON}"; then
  echo "ERROR: hooks.json must use python3, not uv run python (.cursor/hooks/README.md)" >&2
  exit 1
fi

if ! rg -q 'python3 .cursor/hooks/' "${HOOKS_JSON}"; then
  echo "ERROR: hooks.json must invoke hooks via python3 .cursor/hooks/…" >&2
  exit 1
fi

echo "OK: Cursor hooks use python3 entrypoints."
