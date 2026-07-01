#!/usr/bin/env bash
# Live drift check: GoTrue still using localhost:3000 for invite redirects (TC-109 live).
# Uses project secret key (SUPABASE_SECRET_KEY) — does NOT require SUPABASE_ACCESS_TOKEN.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

STAGING_ADMIN_ORIGIN="${VECINITA_ADMIN_FRONTEND_URL:-https://vecinita-admin-frontend-ef4ob.ondigitalocean.app}"
PROJECT_REF="${SUPABASE_PROJECT_REF:-cfuvghdsuwactfeamtym}"

if [[ -z "${SUPABASE_SECRET_KEY:-}" ]]; then
  echo "ERROR: SUPABASE_SECRET_KEY is not set." >&2
  exit 1
fi

if [[ -z "${SUPABASE_URL:-}" ]]; then
  SUPABASE_URL="https://${PROJECT_REF}.supabase.co"
fi

redirect_to="${STAGING_ADMIN_ORIGIN}/accept-invite"
test_email="drift-check-$(date +%s)@example.invalid"

echo "==> generate_link probe (redirect_to=${redirect_to})"
response="$(curl -fsS -X POST "${SUPABASE_URL}/auth/v1/admin/generate_link" \
  -H "apikey: ${SUPABASE_SECRET_KEY}" \
  -H "Authorization: Bearer ${SUPABASE_SECRET_KEY}" \
  -H "Content-Type: application/json" \
  -d "{\"type\":\"invite\",\"email\":\"${test_email}\",\"redirect_to\":\"${redirect_to}\"}")"

action_link="$(echo "$response" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("action_link",""))')"

echo "    action_link: ${action_link}"

fail=0
if [[ "$action_link" == *"localhost:3000"* ]]; then
  echo "FAIL: GoTrue still embeds localhost:3000 in invite links." >&2
  fail=1
fi
if [[ "$action_link" != *"redirect_to="* ]]; then
  echo "FAIL: action_link missing redirect_to query param." >&2
  fail=1
fi
encoded_redirect="$(python3 -c "import urllib.parse; print(urllib.parse.quote('${redirect_to}', safe=''))")"
if [[ "$action_link" != *"${encoded_redirect}"* && "$action_link" != *"redirect_to=${STAGING_ADMIN_ORIGIN}"* ]]; then
  echo "FAIL: redirect_to was not honored (staging /accept-invite missing)." >&2
  echo "      live redirect_to param likely fell back to site_url." >&2
  fail=1
fi

if [[ "$fail" -eq 1 ]]; then
  echo >&2
  echo "Remediation (requires Supabase personal access token, not project secret key):" >&2
  echo "  export SUPABASE_ACCESS_TOKEN=sbp_...   # https://supabase.com/dashboard/account/tokens" >&2
  echo "  bash scripts/supabase/apply_auth_config_from_toml.sh" >&2
  echo "  bash scripts/supabase/verify_live_auth_urls.sh" >&2
  exit 1
fi

echo "OK: live GoTrue invite links use staging admin redirect URLs."
