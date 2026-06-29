#!/usr/bin/env bash
# Sync the Modal `vecinita-data-management` secret from the current shell env.
#
# Reads values from the environment (source prod.env first) and pushes them with
# `modal secret create --force` (merges keys; does not drop unlisted keys).
# Keys checklist: infra/modal/.env.example. Matrix: docs/staging-secrets-matrix.md.
#
# Usage:
#   set -a && source prod.env && set +a
#   bash scripts/deploy/sync_modal_secret.sh            # dry run (prints keys)
#   bash scripts/deploy/sync_modal_secret.sh --apply    # write the secret
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

APPLY=0
[[ "${1:-}" == "--apply" ]] && APPLY=1

# shellcheck source=../modal_ensure_workspace.sh
source "${ROOT}/scripts/modal_ensure_workspace.sh"

SECRET_NAME="vecinita-data-management"

# Required keys for the data-management ASGI app (infra/modal/data_management_app.py).
REQUIRED_KEYS=(
  VECINITA_MODAL_EMBED_URL
  VECINITA_MODAL_LLM_URL
  VECINITA_INTERNAL_WRITE_URL
  VECINITA_INTERNAL_API_KEY
  VECINITA_MODAL_PROXY_KEY
  VECINITA_CORS_ORIGINS
  SUPABASE_URL
)
# Optional keys (only pushed when set in the shell).
OPTIONAL_KEYS=(
  VECINITA_AUTH_REQUIRED
  SUPABASE_JWT_AUD
  VECINITA_LLM_TAG_MAX_TOKENS
  VECINITA_TAG_SEED_PATH
)

# DATABASE_URL is forbidden on Modal (ADR-007 — sole holder is the DO write API).
if [[ -n "${DATABASE_URL:-}" ]]; then
  echo "WARN: DATABASE_URL is set in the shell — it will NOT be pushed to Modal (ADR-007)." >&2
fi

PAIRS=()
MISSING=()
for key in "${REQUIRED_KEYS[@]}"; do
  val="${!key:-}"
  if [[ -z "$val" ]]; then
    MISSING+=("$key")
    continue
  fi
  PAIRS+=("$key=$val")
done

# Default VECINITA_AUTH_REQUIRED to true when unset (EV-005 F34 — ADR-028).
if [[ -z "${VECINITA_AUTH_REQUIRED:-}" ]]; then
  PAIRS+=("VECINITA_AUTH_REQUIRED=true")
  echo "==> VECINITA_AUTH_REQUIRED unset; defaulting to 'true'"
fi

for key in "${OPTIONAL_KEYS[@]}"; do
  val="${!key:-}"
  [[ -n "$val" ]] && PAIRS+=("$key=$val")
done

if [[ ${#MISSING[@]} -gt 0 ]]; then
  echo "ERROR: missing required env vars for ${SECRET_NAME}:" >&2
  printf '  - %s\n' "${MISSING[@]}" >&2
  echo "Source prod.env (set -a && source prod.env && set +a). See infra/modal/.env.example." >&2
  exit 1
fi

echo "==> Modal secret: ${SECRET_NAME}"
echo "    Keys to push (values hidden):"
for pair in "${PAIRS[@]}"; do
  echo "      - ${pair%%=*}"
done

if [[ "$APPLY" -ne 1 ]]; then
  echo "Dry run. Re-run with --apply to write the secret."
  exit 0
fi

modal secret create --force "${SECRET_NAME}" "${PAIRS[@]}"
echo "OK: updated Modal secret ${SECRET_NAME}."
echo "Redeploy to pick up changes: bash scripts/deploy/modal.sh"
