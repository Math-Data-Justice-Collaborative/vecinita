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

require_env() {
  local key="$1"
  if [[ -z "${!key:-}" ]]; then
    echo "ERROR: ${key} is required." >&2
    exit 1
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

prepare_staging_config_root() {
  local project_ref="$1"
  local admin_origin="$2"
  local sender_email="$3"
  local temp_root

  temp_root="$(mktemp -d)"
  cp -R "$ROOT/supabase" "$temp_root/"

  TMP_SUPABASE_CONFIG_ROOT="$temp_root" \
  TMP_SUPABASE_PROJECT_REF="$project_ref" \
  TMP_SUPABASE_ADMIN_ORIGIN="$admin_origin" \
  TMP_SUPABASE_ADMIN_EMAIL="$sender_email" \
  python3 <<'PY'
from __future__ import annotations

import os
import re
from pathlib import Path

root = Path(os.environ["TMP_SUPABASE_CONFIG_ROOT"])
project_ref = os.environ["TMP_SUPABASE_PROJECT_REF"]
admin_origin = os.environ["TMP_SUPABASE_ADMIN_ORIGIN"].rstrip("/")
admin_email = os.environ["TMP_SUPABASE_ADMIN_EMAIL"]
config_path = root / "supabase" / "config.toml"
text = config_path.read_text(encoding="utf-8")

project_pattern = re.compile(r'^project_id\s*=\s*"[^"]+"', re.M)
site_pattern = re.compile(r'^site_url\s*=\s*"([^"]+)"', re.M)
email_pattern = re.compile(
    r'(\[auth\.email\.smtp\]\s+enabled = true\s+host = "smtp\.resend\.com"\s+'
    r'port = 465\s+user = "resend"\s+pass = "env\(SUPABASE_SMTP_PASS\)"\s+'
    r'admin_email = )"[^"]+"',
    re.S,
)
redirect_block_pattern = re.compile(
    r"(additional_redirect_urls\s*=\s*\[)(.*?)(\n\])",
    re.S,
)

site_match = site_pattern.search(text)
if site_match is None:
    raise SystemExit("site_url not found in supabase/config.toml")
old_origin = site_match.group(1).rstrip("/")

text = project_pattern.sub(f'project_id = "{project_ref}"', text, count=1)
text = site_pattern.sub(f'site_url = "{admin_origin}"', text, count=1)

redirect_match = redirect_block_pattern.search(text)
if redirect_match is None:
    raise SystemExit("additional_redirect_urls block not found in supabase/config.toml")

redirects = re.findall(r'"([^"]+)"', redirect_match.group(2))
rewritten: list[str] = []
seen: set[str] = set()
for entry in redirects:
    updated = entry
    if entry == old_origin:
        updated = admin_origin
    elif entry.startswith(f"{old_origin}/"):
        updated = f"{admin_origin}{entry[len(old_origin):]}"
    if updated not in seen:
        rewritten.append(updated)
        seen.add(updated)

redirect_lines = "".join(f'\n  "{entry}",' for entry in rewritten)
text = redirect_block_pattern.sub(
    r"\1" + redirect_lines + r"\3",
    text,
    count=1,
)

if email_pattern.search(text) is None:
    raise SystemExit("[auth.email.smtp] admin_email not found in supabase/config.toml")
text = email_pattern.sub(rf'\1"{admin_email}"', text, count=1)

config_path.write_text(text, encoding="utf-8")
print(root / "supabase")
PY
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
  # Expired/revoked Management API PATs must not block Modal/DO CD. Same soft-fail
  # pattern as scripts/security/run-supabase-advisors.sh (Unauthorized → skip).
  set +e
  link_log="$(link_project 2>&1)"
  link_rc=$?
  set -e
  if (( link_rc != 0 )); then
    if grep -qiE 'unauthorized|401' <<<"$link_log"; then
      echo "WARN: SUPABASE_ACCESS_TOKEN unauthorized — skipping production sync." >&2
      echo "Rotate the account PAT in GitHub Actions secrets (Settings → Secrets)." >&2
      echo "$link_log" >&2
      exit 0
    fi
    echo "$link_log" >&2
    exit "$link_rc"
  fi
  printf '%s\n' "$link_log"
  echo "==> Pushing auth/config from supabase/config.toml"
  supabase config push --yes
  if compgen -G "supabase/migrations/*.sql" > /dev/null; then
    echo "==> Applying SQL migrations to linked project"
    supabase db push --yes
  else
    echo "No supabase/migrations/*.sql — skipping db push"
  fi
}

sync_staging() {
  require_env "SUPABASE_ACCESS_TOKEN"
  require_env "SUPABASE_SMTP_PASS"
  require_env "SUPABASE_SECRET_KEY"
  require_env "SUPABASE_URL"
  require_env "RESEND_SENDER_EMAIL"
  require_env "VECINITA_ADMIN_FRONTEND_URL"

  local project_ref="${SUPABASE_PROJECT_REF:-${SUPABASE_PROJECT_ID:-}}"
  if [[ -z "$project_ref" ]]; then
    project_ref="$(branch_project_ref_from_url "${SUPABASE_URL}")"
  fi
  if [[ -z "$project_ref" ]]; then
    echo "ERROR: could not derive staging SUPABASE_PROJECT_REF from SUPABASE_URL" >&2
    exit 1
  fi

  local admin_origin="${VECINITA_ADMIN_FRONTEND_URL%/}"
  local staging_root
  local previous_dir="$PWD"
  staging_root="$(prepare_staging_config_root "$project_ref" "$admin_origin" "${RESEND_SENDER_EMAIL}")"
  trap 'rm -rf "$staging_root"' RETURN

  PROJECT_REF="$project_ref"
  cd "$staging_root"
  link_project
  echo "==> Pushing staging auth/config from temp config.toml"
  supabase config push --project-ref "$PROJECT_REF" --yes
  if compgen -G "supabase/migrations/*.sql" > /dev/null; then
    echo "==> Applying SQL migrations to staging project"
    supabase db push --yes
  else
    echo "No supabase/migrations/*.sql — skipping db push"
  fi
  echo "==> Verifying staging auth URL config"
  VECINITA_ADMIN_FRONTEND_URL="$admin_origin" \
  SUPABASE_PROJECT_REF="$project_ref" \
  SUPABASE_URL="${SUPABASE_URL}" \
  SUPABASE_SECRET_KEY="${SUPABASE_SECRET_KEY}" \
  bash "$ROOT/scripts/supabase/verify_live_auth_urls.sh"
  VECINITA_ADMIN_FRONTEND_URL="$admin_origin" \
  SUPABASE_PROJECT_REF="$project_ref" \
  SUPABASE_URL="${SUPABASE_URL}" \
  SUPABASE_SECRET_KEY="${SUPABASE_SECRET_KEY}" \
  bash "$ROOT/scripts/supabase/check_live_invite_redirect.sh"
  cd "$previous_dir"
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
  sync-staging             Push config (+ migrations) to the staging project
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
    sync-staging) sync_staging ;;
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
