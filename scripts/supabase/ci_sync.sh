#!/usr/bin/env bash
# Supabase remote sync helpers for GitHub Actions (ADR-027 §6).
# Requires SUPABASE_ACCESS_TOKEN and SUPABASE_PROJECT_REF in the environment.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

PROJECT_REF="${SUPABASE_PROJECT_REF:-cfuvghdsuwactfeamtym}"

require_token() {
  if [[ -z "${SUPABASE_ACCESS_TOKEN:-}" ]]; then
    echo "SKIP: SUPABASE_ACCESS_TOKEN not set — cloud sync disabled."
    exit 0
  fi
}

link_project() {
  require_token
  if [[ -n "${SUPABASE_DB_PASSWORD:-}" ]]; then
    supabase link --project-ref "$PROJECT_REF" --password "$SUPABASE_DB_PASSWORD"
  else
    supabase link --project-ref "$PROJECT_REF"
  fi
}

sync_production() {
  require_token
  link_project
  echo "==> Pushing auth/config from supabase/config.toml"
  supabase config push
  if compgen -G "supabase/migrations/*.sql" > /dev/null; then
    echo "==> Applying SQL migrations to linked project"
    supabase db push
  else
    echo "No supabase/migrations/*.sql — skipping db push"
  fi
}

preview_branch() {
  require_token
  local branch_name="${1:-}"
  if [[ -z "$branch_name" ]]; then
    echo "ERROR: preview branch name required" >&2
    exit 1
  fi
  echo "==> Creating ephemeral preview branch: ${branch_name}"
  supabase branches create "$branch_name" --experimental
  link_project
  if compgen -G "supabase/migrations/*.sql" > /dev/null; then
    supabase db push
  fi
  supabase config push
  echo "Preview branch ${branch_name} ready for review."
}

delete_preview_branch() {
  require_token
  local branch_name="${1:-}"
  if [[ -z "$branch_name" ]]; then
    echo "ERROR: preview branch name required" >&2
    exit 1
  fi
  echo "==> Deleting preview branch: ${branch_name}"
  supabase branches delete "$branch_name" --experimental || true
}

usage() {
  cat <<EOF
Usage: $(basename "$0") <command> [args]

Commands:
  sync-production          Push config (+ migrations when present) to canonical project
  preview-branch <name>    Create ephemeral preview branch and apply repo state
  delete-preview <name>    Tear down an ephemeral preview branch

Environment:
  SUPABASE_ACCESS_TOKEN    Required for cloud commands (skip gracefully when unset)
  SUPABASE_PROJECT_REF     Default: ${PROJECT_REF}
  SUPABASE_DB_PASSWORD     Optional — passed to supabase link when set
EOF
}

main() {
  local cmd="${1:-}"
  shift || true
  case "$cmd" in
    sync-production) sync_production ;;
    preview-branch) preview_branch "${1:-}" ;;
    delete-preview) delete_preview_branch "${1:-}" ;;
    -h | --help | help) usage ;;
    *)
      echo "ERROR: unknown command: ${cmd:-}" >&2
      usage >&2
      exit 1
      ;;
  esac
}

main "$@"
