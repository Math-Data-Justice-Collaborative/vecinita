#!/usr/bin/env bash
# Parse-only loader for Supabase Management API credentials.
# Never `source`s .env / prod.env — extracts keys with grep only.
#
# Usage (source into caller):
#   # shellcheck source=scripts/security/load_supabase_credentials.sh
#   source "${ROOT}/scripts/security/load_supabase_credentials.sh"
#   vecinita_load_supabase_credentials "${ROOT}"
#
# Usage (eval export lines):
#   eval "$(bash scripts/security/load_supabase_credentials.sh --export [--root DIR])"
set -euo pipefail

vecinita_load_env_key() {
  local key="$1" file="$2"
  [[ -f "${file}" ]] || return 0
  local line
  line="$(grep -E "^${key}=" "${file}" | tail -1 || true)"
  [[ -n "${line}" ]] || return 0
  printf '%s' "${line#*=}" | sed 's/^["'\'']//; s/["'\'']$//'
}

vecinita_load_supabase_credentials() {
  local root="${1:-}"
  if [[ -z "${root}" ]]; then
    root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
  fi

  if [[ -z "${SUPABASE_ACCESS_TOKEN:-}" ]]; then
    SUPABASE_ACCESS_TOKEN="$(vecinita_load_env_key SUPABASE_ACCESS_TOKEN "${root}/.env")"
  fi
  if [[ -z "${SUPABASE_ACCESS_TOKEN:-}" ]]; then
    SUPABASE_ACCESS_TOKEN="$(vecinita_load_env_key SUPABASE_ACCESS_TOKEN "${root}/prod.env")"
  fi

  if [[ -z "${SUPABASE_PROJECT_REF:-}" ]]; then
    SUPABASE_PROJECT_REF="${SUPABASE_PROJECT_ID:-}"
  fi
  if [[ -z "${SUPABASE_PROJECT_REF:-}" ]]; then
    SUPABASE_PROJECT_REF="$(vecinita_load_env_key SUPABASE_PROJECT_REF "${root}/.env")"
  fi
  if [[ -z "${SUPABASE_PROJECT_REF:-}" ]]; then
    SUPABASE_PROJECT_REF="$(vecinita_load_env_key SUPABASE_PROJECT_REF "${root}/prod.env")"
  fi
  if [[ -z "${SUPABASE_PROJECT_REF:-}" ]]; then
    SUPABASE_PROJECT_REF="$(vecinita_load_env_key SUPABASE_PROJECT_ID "${root}/.env")"
  fi
  if [[ -z "${SUPABASE_PROJECT_REF:-}" ]]; then
    SUPABASE_PROJECT_REF="$(vecinita_load_env_key SUPABASE_PROJECT_ID "${root}/prod.env")"
  fi
  if [[ -z "${SUPABASE_PROJECT_REF:-}" && -f "${root}/supabase/config.toml" ]]; then
    SUPABASE_PROJECT_REF="$(
      sed -n 's/^project_id[[:space:]]*=[[:space:]]*"\([^"]*\)".*/\1/p' \
        "${root}/supabase/config.toml" | head -1
    )"
  fi

  export SUPABASE_ACCESS_TOKEN="${SUPABASE_ACCESS_TOKEN:-}"
  export SUPABASE_PROJECT_REF="${SUPABASE_PROJECT_REF:-}"
}

# CLI mode when executed (not sourced).
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  ROOT_ARG=""
  DO_EXPORT=0
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --export) DO_EXPORT=1; shift ;;
      --root)
        ROOT_ARG="${2:-}"
        shift 2
        ;;
      *)
        echo "usage: $0 [--export] [--root DIR]" >&2
        exit 2
        ;;
    esac
  done
  vecinita_load_supabase_credentials "${ROOT_ARG}"
  if [[ "${DO_EXPORT}" -eq 1 ]]; then
    # Print KEY=value lines for tests / eval (values may contain secrets — do not log).
    printf 'SUPABASE_ACCESS_TOKEN=%s\n' "${SUPABASE_ACCESS_TOKEN}"
    printf 'SUPABASE_PROJECT_REF=%s\n' "${SUPABASE_PROJECT_REF}"
  fi
fi
