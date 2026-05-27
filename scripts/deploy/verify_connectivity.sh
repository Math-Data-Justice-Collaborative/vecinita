#!/usr/bin/env bash
# H4/H5 connectivity gate — browser CORS + frontend bundle wiring.
# See .cursor/skills/connectivity-gates.md
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT"

echo "==> H0c local CORS policy tests (incl. TC-046 browse GET, TC-049 admin PATCH, TC-060 EV-002)"
uv run pytest tests/unit/test_cors_policy.py tests/unit/test_cors_ev002.py -q

CHAT_API="${VECINITA_STAGING_CHAT_URL:-}"
CHAT_FE="${VECINITA_STAGING_CHAT_FRONTEND_URL:-}"
WRITE_API="${VECINITA_STAGING_WRITE_URL:-}"
ADMIN_FE="${VECINITA_STAGING_ADMIN_FRONTEND_URL:-}"
ADMIN_API="${VECINITA_STAGING_ADMIN_API_URL:-}"

if [[ -z "$CHAT_API" && -z "$CHAT_FE" && -z "$WRITE_API" && -z "$ADMIN_FE" ]]; then
  echo "SKIP live H4/H5: set VECINITA_STAGING_* URLs (see connectivity-gates.md)"
  exit 0
fi

echo "==> H4/H5 live staging connectivity pytest (browse, admin PATCH, EV-002 bulk/stats/audit)"
export VECINITA_STAGING_CHAT_URL="$CHAT_API"
export VECINITA_STAGING_CHAT_FRONTEND_URL="$CHAT_FE"
export VECINITA_STAGING_WRITE_URL="$WRITE_API"
export VECINITA_STAGING_ADMIN_FRONTEND_URL="$ADMIN_FE"
export VECINITA_STAGING_ADMIN_API_URL="$ADMIN_API"
uv run pytest tests/smoke/test_staging_connectivity.py -m live -q

echo "OK: connectivity gates passed."
