#!/usr/bin/env bash
# Supabase remote sync helpers for GitHub Actions (ADR-027 §6).
# Requires SUPABASE_ACCESS_TOKEN and SUPABASE_PROJECT_REF (or SUPABASE_PROJECT_ID).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

# Supabase docs use SUPABASE_PROJECT_ID; repo workflow also sets SUPABASE_PROJECT_REF.
PROJECT_REF="${SUPABASE_PROJECT_REF:-${SUPABASE_PROJECT_ID:-cfuvghdsuwactfeamtym}}"

require_token() {
  if [[ -z "${SUPABASE_ACCESS_TOKEN:-}" ]]; then
    echo "SKIP: SUPABASE_ACCESS_TOKEN not set — cloud sync disabled."
    exit 0
  fi
}

require_jq() {
  if ! command -v jq >/dev/null 2>&1; then
    echo "ERROR: jq is required for preview branch sync" >&2
    exit 1
  fi
}

link_project() {
  require_token
  if [[ -n "${SUPABASE_DB_PASSWORD:-}" ]]; then
    supabase link --project-ref "$PROJECT_REF" --password "$SUPABASE_DB_PASSWORD" --yes
  else
    supabase link --project-ref "$PROJECT_REF" --yes
  fi
}

branch_project_ref_from_url() {
  local url="$1"
  sed -n 's|https://\([^.]*\)\.supabase\.co.*|\1|p' <<<"$url"
}

preview_branch_exists() {
  local branch_name="$1"
  supabase branches get "$branch_name" --project-ref "$PROJECT_REF" --experimental -o json >/dev/null 2>&1
}

wait_for_preview_branch() {
  local branch_name="$1"
  local attempts="${PREVIEW_BRANCH_READY_ATTEMPTS:-30}"
  local delay_seconds="${PREVIEW_BRANCH_READY_DELAY_SECONDS:-10}"
  local attempt=0
  local details=""

  while (( attempt < attempts )); do
    if details="$(supabase branches get "$branch_name" --project-ref "$PROJECT_REF" --experimental -o json 2>/dev/null)"; then
      if jq -e '.POSTGRES_URL // empty | length > 0' <<<"$details" >/dev/null; then
        printf '%s' "$details"
        return 0
      fi
    fi
    attempt=$((attempt + 1))
    echo "Waiting for preview branch ${branch_name} to become ready (${attempt}/${attempts})..."
    sleep "$delay_seconds"
  done

  echo "ERROR: preview branch ${branch_name} did not become ready in time" >&2
  exit 1
}

apply_repo_state_to_preview_branch() {
  local branch_name="$1"
  require_jq
  local branch_json db_url branch_ref supabase_url

  branch_json="$(wait_for_preview_branch "$branch_name")"
  db_url="$(jq -r '.POSTGRES_URL // empty' <<<"$branch_json")"
  supabase_url="$(jq -r '.SUPABASE_URL // empty' <<<"$branch_json")"
  branch_ref="$(branch_project_ref_from_url "$supabase_url")"

  if [[ -z "$db_url" || -z "$branch_ref" ]]; then
    echo "ERROR: could not resolve preview branch connection details for ${branch_name}" >&2
    exit 1
  fi

  echo "==> Applying repo state to preview branch ${branch_name} (project ref ${branch_ref})"
  if compgen -G "supabase/migrations/*.sql" > /dev/null; then
    supabase db push --db-url "$db_url" --yes
  fi
  supabase config push --project-ref "$branch_ref" --yes
}

sync_production() {
  require_token
  link_project
  echo "==> Pushing auth/config from supabase/config.toml"
  supabase config push --yes
  if compgen -G "supabase/migrations/*.sql" > /dev/null; then
    echo "==> Applying SQL migrations to linked project"
    supabase db push --yes
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
  link_project
  if preview_branch_exists "$branch_name"; then
    echo "==> Preview branch already exists: ${branch_name}"
  else
    echo "==> Creating ephemeral preview branch: ${branch_name}"
    supabase branches create "$branch_name" --project-ref "$PROJECT_REF" --experimental --yes
  fi
  apply_repo_state_to_preview_branch "$branch_name"
  echo "Preview branch ${branch_name} ready for review."
}

delete_preview_branch() {
  require_token
  local branch_name="${1:-}"
  if [[ -z "$branch_name" ]]; then
    echo "ERROR: preview branch name required" >&2
    exit 1
  fi
  link_project
  echo "==> Deleting preview branch: ${branch_name}"
  supabase branches delete "$branch_name" --project-ref "$PROJECT_REF" --experimental --yes || true
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
  SUPABASE_PROJECT_REF     Canonical project ref (default: cfuvghdsuwactfeamtym)
  SUPABASE_PROJECT_ID      Alias for SUPABASE_PROJECT_REF (Supabase docs convention)
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
