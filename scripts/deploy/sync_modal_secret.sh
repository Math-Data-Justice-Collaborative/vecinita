#!/usr/bin/env bash
# Sync the Modal `vecinita-data-management` secret from the current shell env.
#
# Reads values from the environment (source prod.env first) and pushes them with
# `modal secret create --force`.
#
# IMPORTANT: `modal secret create --force` REPLACES the whole secret (it does not
# merge). To add a key (e.g. EV-006 SUPABASE_SECRET_KEY) without dropping the
# existing production keys, use --merge: it first exports the live secret, layers
# the shell env on top, then re-pushes the union.
#
# Keys checklist: infra/modal/.env.example. Matrix: docs/staging-secrets-matrix.md.
#
# Usage:
#   set -a && source prod.env && set +a
#   bash scripts/deploy/sync_modal_secret.sh            # dry run (prints keys)
#   bash scripts/deploy/sync_modal_secret.sh --apply    # REPLACE from shell env only
#   bash scripts/deploy/sync_modal_secret.sh --merge            # dry run, union with live secret
#   bash scripts/deploy/sync_modal_secret.sh --merge --apply    # safe add/update of keys
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

APPLY=0
MERGE=0
for arg in "$@"; do
  case "$arg" in
    --apply) APPLY=1 ;;
    --merge) MERGE=1 ;;
  esac
done

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
  SUPABASE_SECRET_KEY   # EV-006 F35 — Admin API for /admin/users* (ADR-030 / TP-S005-01)
  RESEND_API_KEY        # EV-006 F35 — Resend REST test-send (ADR-031 / TP-S005-22)
  RESEND_SENDER_EMAIL   # verified sender (= config.toml admin_email)
  VECINITA_LLM_TAG_MAX_TOKENS
  VECINITA_TAG_SEED_PATH
)

# --merge: export the live secret and seed the shell env with any keys not already
# set locally, so a re-push is the UNION (existing keys preserved, shell wins on conflict).
if [[ "$MERGE" -eq 1 ]]; then
  echo "==> --merge: reading live ${SECRET_NAME:-vecinita-data-management} secret to preserve existing keys"
  EXPORT_FILE="${ROOT}/.tmp/modal-${SECRET_NAME:-vecinita-data-management}.env"
  mkdir -p "${ROOT}/.tmp"
  if uv run --with modal modal run scripts/deploy/export_modal_secret.py >/dev/null 2>&1; then
    : # export script writes EXPORT_FILE
  fi
  if [[ -f "$EXPORT_FILE" ]]; then
    # Seed only keys that are NOT already set in the shell (shell/prod.env takes precedence).
    while IFS='=' read -r k v; do
      [[ -z "$k" || "$k" == \#* ]] && continue
      if [[ -z "${!k:-}" ]]; then
        export "$k=$v"
      fi
    done < "$EXPORT_FILE"
    echo "    merged live keys from ${EXPORT_FILE#"$ROOT"/}"
  else
    echo "WARN: could not export live secret; proceeding with shell env only." >&2
  fi
fi

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

# When Resend test-send key is present, default sender to config.toml admin_email if unset.
if [[ -n "${RESEND_API_KEY:-}" && -z "${RESEND_SENDER_EMAIL:-}" ]]; then
  PAIRS+=("RESEND_SENDER_EMAIL=noreply@vecinita.admin")
  echo "==> RESEND_SENDER_EMAIL unset; defaulting to 'noreply@vecinita.admin' (config.toml admin_email)"
fi

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
