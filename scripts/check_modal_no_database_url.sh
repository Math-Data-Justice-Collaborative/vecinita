#!/usr/bin/env bash
# ADR-007: Modal workers must not hold DATABASE_URL (Phase 2 gate, T13.4).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGETS=(
  "$ROOT/infra/modal"
  "$ROOT/apps/data-management-backend"
)

if rg -n 'DATABASE_URL' "${TARGETS[@]}" --glob '*.py' 2>/dev/null; then
  echo "ERROR: DATABASE_URL found in Modal worker paths (ADR-007)." >&2
  exit 1
fi

echo "OK: no DATABASE_URL in Modal Python paths."
