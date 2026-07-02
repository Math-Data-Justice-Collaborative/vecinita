#!/usr/bin/env bash
# Materialize deployment env vars in GitHub Actions from repository secrets.
#
# Workflows inject secrets into the job env; this script derives aliases so
# sync_modal_secret.sh and do_apps.py sync-all-secrets can run without prod.env.
#
# Usage (in CI after secrets are mapped to env):
#   bash scripts/deploy/ci_materialize_env.sh
#   bash scripts/deploy/ci_materialize_env.sh --check modal
#   bash scripts/deploy/ci_materialize_env.sh --check do
#   bash scripts/deploy/ci_materialize_env.sh --check alembic
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

CHECK_TARGET="${1:-}"

# prod.env naming aliases
if [[ -z "${SUPABASE_DB_PASSWORD:-}" && -n "${SUPABASE_DATABASE_PASSWORD:-}" ]]; then
  export SUPABASE_DB_PASSWORD="${SUPABASE_DATABASE_PASSWORD}"
fi
if [[ -z "${SUPABASE_SMTP_PASS:-}" && -n "${RESEND_API_KEY:-}" ]]; then
  export SUPABASE_SMTP_PASS="${RESEND_API_KEY}"
fi

# VITE_* build-time aliases (admin + chat frontends)
export VITE_SUPABASE_URL="${VITE_SUPABASE_URL:-${SUPABASE_URL:-}}"
export VITE_SUPABASE_PUBLISHABLE_KEY="${VITE_SUPABASE_PUBLISHABLE_KEY:-${SUPABASE_PUBLISHABLE_KEY:-}}"
export VITE_VECINITA_CORPUS_API_KEY="${VITE_VECINITA_CORPUS_API_KEY:-${VECINITA_INTERNAL_API_KEY:-}}"
export VITE_VECINITA_MODAL_PROXY_KEY="${VITE_VECINITA_MODAL_PROXY_KEY:-${VECINITA_MODAL_PROXY_KEY:-}}"

# Shared service URLs (Modal secret + DO backends)
export VECINITA_INTERNAL_WRITE_URL="${VECINITA_INTERNAL_WRITE_URL:-${VECINITA_STAGING_WRITE_URL:-}}"

# CORS: derive from frontend URLs when not set explicitly
if [[ -z "${VECINITA_CORS_ORIGINS:-}" ]]; then
  cors_parts=()
  admin_origin="${VECINITA_ADMIN_FRONTEND_URL:-${VECINITA_STAGING_ADMIN_FRONTEND_URL:-}}"
  chat_origin="${VECINITA_CHAT_FRONTEND_URL:-${VECINITA_STAGING_CHAT_FRONTEND_URL:-}}"
  [[ -n "$admin_origin" ]] && cors_parts+=("$admin_origin")
  [[ -n "$chat_origin" ]] && cors_parts+=("$chat_origin")
  if [[ ${#cors_parts[@]} -gt 0 ]]; then
    export VECINITA_CORS_ORIGINS="$(IFS=,; echo "${cors_parts[*]}")"
  fi
fi

_missing() {
  local label="$1"
  shift
  local missing=()
  for key in "$@"; do
    [[ -z "${!key:-}" ]] && missing+=("$key")
  done
  if [[ ${#missing[@]} -gt 0 ]]; then
    echo "WARN: ${label} — missing env: ${missing[*]}" >&2
    return 1
  fi
  return 0
}

case "$CHECK_TARGET" in
  --check)
    target="${2:-}"
    case "$target" in
      modal)
        _missing "Modal sync" \
          VECINITA_MODAL_EMBED_URL VECINITA_MODAL_LLM_URL VECINITA_INTERNAL_WRITE_URL \
          VECINITA_INTERNAL_API_KEY VECINITA_MODAL_PROXY_KEY VECINITA_CORS_ORIGINS SUPABASE_URL
        ;;
      do)
        _missing "DO sync" \
          DATABASE_URL VECINITA_INTERNAL_API_KEY VECINITA_CORS_ORIGINS SUPABASE_URL \
          VECINITA_MODAL_EMBED_URL VECINITA_MODAL_LLM_URL VECINITA_MODAL_DATA_MGMT_URL
        if [[ -n "${VECINITA_MODAL_EMBED_URL:-}" ]]; then
          uv run python scripts/deploy/modal_url_validate.py \
            VECINITA_MODAL_EMBED_URL "${VECINITA_MODAL_EMBED_URL}"
        fi
        if [[ -n "${VECINITA_MODAL_LLM_URL:-}" ]]; then
          uv run python scripts/deploy/modal_url_validate.py \
            VECINITA_MODAL_LLM_URL "${VECINITA_MODAL_LLM_URL}"
        fi
        ;;
      alembic)
        _missing "Alembic upgrade" DATABASE_URL
        ;;
      *)
        echo "Usage: $0 --check {modal|do|alembic}" >&2
        exit 2
        ;;
    esac
    ;;
  "")
    echo "CI env materialized (values hidden)."
    ;;
  *)
    echo "Unknown arg: $CHECK_TARGET" >&2
    exit 2
    ;;
esac
