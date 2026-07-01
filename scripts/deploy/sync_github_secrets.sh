#!/usr/bin/env bash
# Sync GitHub Actions repository secrets from the current shell env (source prod.env first).
#
# Consumed by .github/workflows/{ci,supabase,deploy-modal,deploy-digitalocean,deploy-preflight}.yml.
# Master secret store: repo-root prod.env (gitignored). Template: infra/github/.env.example.
# Matrix: docs/staging-secrets-matrix.md §GitHub Actions.
#
# Usage:
#   set -a && source prod.env && set +a
#   bash scripts/deploy/sync_github_secrets.sh                 # dry run (state per key)
#   bash scripts/deploy/sync_github_secrets.sh --apply         # gh secret set for present keys
#   REPO=owner/name bash scripts/deploy/sync_github_secrets.sh --apply
#
# Requires: gh (authenticated with `repo` scope). NEVER commit real secrets to git.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

APPLY=0
[[ "${1:-}" == "--apply" ]] && APPLY=1

REPO="${REPO:-Math-Data-Justice-Collaborative/vecinita}"

if ! command -v gh >/dev/null 2>&1; then
  echo "ERROR: gh CLI not found." >&2
  exit 1
fi
if ! gh auth status >/dev/null 2>&1; then
  echo "ERROR: gh is not authenticated (gh auth login)." >&2
  exit 1
fi

# prod.env stores the Supabase DB password under a different name — map it.
if [[ -z "${SUPABASE_DB_PASSWORD:-}" && -n "${SUPABASE_DATABASE_PASSWORD:-}" ]]; then
  SUPABASE_DB_PASSWORD="${SUPABASE_DATABASE_PASSWORD}"
  export SUPABASE_DB_PASSWORD
fi
# prod.env may store the Resend API key as RESEND_API_KEY; GitHub/supabase.yml expect SUPABASE_SMTP_PASS.
if [[ -z "${SUPABASE_SMTP_PASS:-}" && -n "${RESEND_API_KEY:-}" ]]; then
  SUPABASE_SMTP_PASS="${RESEND_API_KEY}"
  export SUPABASE_SMTP_PASS
fi
# SUPABASE_PROJECT_ID falls back to the canonical ref when unset.
: "${SUPABASE_PROJECT_ID:=cfuvghdsuwactfeamtym}"
export SUPABASE_PROJECT_ID

# Secrets to manage (present-in-shell keys are pushed; missing keys are reported, not failed).
KEYS=(
  DIGITALOCEAN_TOKEN
  MODAL_TOKEN_ID
  MODAL_TOKEN_SECRET
  SUPABASE_ACCESS_TOKEN
  SUPABASE_DB_PASSWORD
  SUPABASE_PROJECT_ID
  SUPABASE_URL
  SUPABASE_PUBLISHABLE_KEY
  SUPABASE_SECRET_KEY
  SUPABASE_ADMIN_EMAIL
  SUPABASE_ADMIN_PASSWORD
  SUPABASE_SMTP_PASS   # EV-006 F35 — Resend API key; resolves config.toml env(SUPABASE_SMTP_PASS)
  RESEND_API_KEY       # same value as SUPABASE_SMTP_PASS for Modal test-send
  RESEND_SENDER_EMAIL
  # Postgres + cross-service auth (CI alembic + DO/Modal sync)
  DATABASE_URL
  VECINITA_INTERNAL_API_KEY
  VECINITA_CORS_ORIGINS
  VECINITA_MODAL_EMBED_URL
  VECINITA_MODAL_LLM_URL
  VECINITA_MODAL_DATA_MGMT_URL
  VECINITA_MODAL_PROXY_KEY
  VECINITA_INTERNAL_WRITE_URL
  VECINITA_CHAT_RAG_URL
  VECINITA_CHAT_FRONTEND_URL
  VECINITA_ADMIN_FRONTEND_URL
  VECINITA_STATS_ENABLED
  # DO static site BUILD_TIME (admin + chat frontends)
  VITE_VECINITA_ADMIN_API_URL
  VITE_VECINITA_CORPUS_API_URL
  VITE_VECINITA_CHAT_API_URL
  VITE_VECINITA_MODAL_PROXY_KEY
  VITE_VECINITA_CORPUS_API_KEY
  VITE_SUPABASE_URL
  VITE_SUPABASE_PUBLISHABLE_KEY
)

echo "=================================================="
echo " GitHub Actions secret sync — repo: ${REPO}"
echo " mode: $([[ $APPLY -eq 1 ]] && echo APPLY || echo 'DRY RUN')"
echo "=================================================="

existing="$(gh secret list -R "$REPO" --json name -q '.[].name' 2>/dev/null || true)"

present=(); missing=()
for key in "${KEYS[@]}"; do
  if [[ -n "${!key:-}" ]]; then present+=("$key"); else missing+=("$key"); fi
done

echo
echo "Keys present in shell (values hidden):"
for key in "${present[@]:-}"; do
  [[ -z "$key" ]] && continue
  state="new"; grep -qx "$key" <<<"$existing" && state="exists→update"
  echo "  + ${key}  (${state})"
done
if [[ ${#missing[@]} -gt 0 ]]; then
  echo
  echo "Keys NOT set in shell (skipped — provide in prod.env to push):"
  for key in "${missing[@]}"; do
    state=""; grep -qx "$key" <<<"$existing" && state="  [already on GitHub]"
    echo "  - ${key}${state}"
  done
fi

if [[ "$APPLY" -ne 1 ]]; then
  echo
  echo "Dry run. Re-run with --apply to write the present keys."
  exit 0
fi

echo
for key in "${present[@]:-}"; do
  [[ -z "$key" ]] && continue
  printf '%s' "${!key}" | gh secret set "$key" -R "$REPO" >/dev/null
  echo "  set ${key}"
done
echo
echo "OK: pushed ${#present[@]} secret(s) to ${REPO}."
echo "Verify: gh secret list -R ${REPO}"
