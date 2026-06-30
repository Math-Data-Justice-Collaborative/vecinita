#!/usr/bin/env bash
# One-shot env/secret sync across every environment for Vecinita.
#
#   GitHub    — push Actions repository secrets (sync_github_secrets.sh).
#   Supabase  — source of truth: validate SUPABASE_URL + JWKS (ES256, ADR-028);
#               optionally bootstrap the first admin (scripts/seed_first_admin.py).
#   Modal     — push the `vecinita-data-management` secret (sync_modal_secret.sh).
#   DigitalOcean — push app env from shell (do_apps.py sync-all-secrets).
#
# Env comes from the shell — load prod.env first (gitignored):
#   set -a && source prod.env && set +a
#   export DIGITALOCEAN_TOKEN='dop_v1_...'
#
# Usage:
#   bash scripts/deploy/sync_env.sh                 # dry run, all environments
#   bash scripts/deploy/sync_env.sh --apply         # write to all environments
#   bash scripts/deploy/sync_env.sh --github --apply # only GitHub Actions secrets
#   bash scripts/deploy/sync_env.sh --modal --apply # only Modal
#   bash scripts/deploy/sync_env.sh --do --apply    # only DigitalOcean
#   bash scripts/deploy/sync_env.sh --supabase --seed-admin --apply
#
# Templates: infra/github/.env.example, supabase/.env.example,
#            infra/do/.env.example, infra/modal/.env.example
# Matrix:    docs/staging-secrets-matrix.md
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

APPLY=0
SEED_ADMIN=0
DO_SUPABASE=0
DO_MODAL=0
DO_DO=0
DO_GITHUB=0

for arg in "$@"; do
  case "$arg" in
    --apply) APPLY=1 ;;
    --seed-admin) SEED_ADMIN=1 ;;
    --supabase) DO_SUPABASE=1 ;;
    --modal) DO_MODAL=1 ;;
    --do) DO_DO=1 ;;
    --github) DO_GITHUB=1 ;;
    -h|--help)
      sed -n '2,21p' "$0" | sed 's/^# \{0,1\}//'
      exit 0
      ;;
    *) echo "Unknown arg: $arg" >&2; exit 2 ;;
  esac
done

# No provider flag => all providers.
if [[ "$DO_SUPABASE" -eq 0 && "$DO_MODAL" -eq 0 && "$DO_DO" -eq 0 && "$DO_GITHUB" -eq 0 ]]; then
  DO_SUPABASE=1; DO_MODAL=1; DO_DO=1; DO_GITHUB=1
fi

MODE="DRY RUN"; [[ "$APPLY" -eq 1 ]] && MODE="APPLY"
echo "=================================================="
echo " Vecinita env sync — mode: ${MODE}"
echo " providers: github=${DO_GITHUB} supabase=${DO_SUPABASE} modal=${DO_MODAL} do=${DO_DO}"
echo "=================================================="

# ---------------------------------------------------------------------------
# Supabase — source of truth (validate, optionally seed admin)
# ---------------------------------------------------------------------------
if [[ "$DO_SUPABASE" -eq 1 ]]; then
  echo
  echo "==> [Supabase] validating SUPABASE_URL + JWKS (ES256, ADR-028)"
  if [[ -z "${SUPABASE_URL:-}" ]]; then
    echo "ERROR: SUPABASE_URL unset. Source prod.env. See infra/modal/.env.example." >&2
    exit 1
  fi
  JWKS_URL="${SUPABASE_URL%/}/auth/v1/.well-known/jwks.json"
  echo "    JWKS: ${JWKS_URL}"
  if command -v curl >/dev/null 2>&1; then
    code="$(curl -s --max-time 15 -o /dev/null -w '%{http_code}' "$JWKS_URL" 2>/dev/null || true)"
    code="${code:-000}"
    if [[ "$code" == "200" ]]; then
      echo "    OK: JWKS reachable (HTTP 200)."
    else
      echo "WARN: JWKS endpoint returned HTTP ${code} — verify SUPABASE_URL." >&2
    fi
  else
    echo "WARN: curl not found — skipped JWKS reachability check." >&2
  fi

  if [[ "$SEED_ADMIN" -eq 1 ]]; then
    : "${SUPABASE_SECRET_KEY:?SUPABASE_SECRET_KEY required for --seed-admin}"
    : "${SUPABASE_ADMIN_EMAIL:?SUPABASE_ADMIN_EMAIL required for --seed-admin}"
    : "${SUPABASE_ADMIN_PASSWORD:?SUPABASE_ADMIN_PASSWORD required for --seed-admin}"
    if [[ "$APPLY" -eq 1 ]]; then
      echo "==> [Supabase] seeding first admin (idempotent)"
      uv run --with httpx python scripts/seed_first_admin.py
    else
      echo "    Dry run: would run scripts/seed_first_admin.py for ${SUPABASE_ADMIN_EMAIL}."
    fi
  fi
fi

# ---------------------------------------------------------------------------
# GitHub Actions — repository secrets
# ---------------------------------------------------------------------------
if [[ "$DO_GITHUB" -eq 1 ]]; then
  echo
  echo "==> [GitHub] sync Actions repository secrets"
  if [[ "$APPLY" -eq 1 ]]; then
    bash scripts/deploy/sync_github_secrets.sh --apply
  else
    bash scripts/deploy/sync_github_secrets.sh
  fi
fi

# ---------------------------------------------------------------------------
# Modal — vecinita-data-management secret
# ---------------------------------------------------------------------------
if [[ "$DO_MODAL" -eq 1 ]]; then
  echo
  echo "==> [Modal] sync vecinita-data-management secret"
  if [[ "$APPLY" -eq 1 ]]; then
    bash scripts/deploy/sync_modal_secret.sh --apply
  else
    bash scripts/deploy/sync_modal_secret.sh
  fi
fi

# ---------------------------------------------------------------------------
# DigitalOcean — all four app specs
# ---------------------------------------------------------------------------
if [[ "$DO_DO" -eq 1 ]]; then
  echo
  echo "==> [DigitalOcean] sync app env (all four apps)"
  if [[ -z "${DIGITALOCEAN_TOKEN:-}" ]]; then
    if [[ "$APPLY" -eq 1 ]]; then
      echo "ERROR: DIGITALOCEAN_TOKEN unset. export DIGITALOCEAN_TOKEN='dop_v1_...'" >&2
      exit 1
    fi
    echo "WARN: DIGITALOCEAN_TOKEN unset — required before --apply." >&2
  fi
  if [[ "$APPLY" -eq 1 ]]; then
    uv run --with pydo --with pyyaml scripts/deploy/do_apps.py sync-all-secrets
    echo "    Note: admin frontend uses BUILD_TIME VITE_* — trigger a redeploy:"
    echo "      uv run --with pydo --with pyyaml scripts/deploy/do_apps.py deploy --name vecinita-admin-frontend"
  else
    echo "    Dry run: would run do_apps.py sync-all-secrets (set --apply to push)."
  fi
fi

echo
echo "=================================================="
if [[ "$APPLY" -eq 1 ]]; then
  echo " Done. Verify: bash scripts/deploy/verify_secrets.sh"
else
  echo " Dry run complete. Re-run with --apply to write changes."
fi
echo "=================================================="
