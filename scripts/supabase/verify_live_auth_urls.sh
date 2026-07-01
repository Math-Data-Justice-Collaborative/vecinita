#!/usr/bin/env bash
# Verify live Supabase auth URL config matches repo contract (TC-109, EV-007).
# Requires SUPABASE_ACCESS_TOKEN (Management API personal access token).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

PROJECT_REF="${SUPABASE_PROJECT_REF:-cfuvghdsuwactfeamtym}"
STAGING_ADMIN_ORIGIN="https://vecinita-admin-frontend-ef4ob.ondigitalocean.app"

if [[ -z "${SUPABASE_ACCESS_TOKEN:-}" ]]; then
  echo "ERROR: SUPABASE_ACCESS_TOKEN is not set." >&2
  echo "  Create at https://supabase.com/dashboard/account/tokens" >&2
  echo "  export SUPABASE_ACCESS_TOKEN=sbp_..." >&2
  exit 1
fi

echo "==> Fetching live auth config for project ${PROJECT_REF}"
response="$(curl -fsS \
  "https://api.supabase.com/v1/projects/${PROJECT_REF}/config/auth" \
  -H "Authorization: Bearer ${SUPABASE_ACCESS_TOKEN}")"

site_url="$(echo "$response" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("site_url",""))')"
uri_allow_list="$(echo "$response" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("uri_allow_list",""))')"
# Management API returns comma- or newline-separated allowlist entries.
normalized_allow_list="$(echo "$uri_allow_list" | tr ',' '\n')"

echo "    site_url: ${site_url}"
echo "    uri_allow_list (first 200 chars): ${uri_allow_list:0:200}..."

fail=0

if [[ "$site_url" != "$STAGING_ADMIN_ORIGIN" ]]; then
  echo "FAIL: site_url must be ${STAGING_ADMIN_ORIGIN}" >&2
  echo "      live value: ${site_url}" >&2
  fail=1
fi

if [[ "$site_url" == *"localhost:3000"* ]]; then
  echo "FAIL: site_url still references localhost:3000" >&2
  fail=1
fi

if [[ "$normalized_allow_list" == *"localhost:3000"* ]]; then
  echo "FAIL: uri_allow_list still references localhost:3000" >&2
  fail=1
fi

for required in \
  "${STAGING_ADMIN_ORIGIN}" \
  "${STAGING_ADMIN_ORIGIN}/accept-invite" \
  "${STAGING_ADMIN_ORIGIN}/reset-password"; do
  if [[ "$normalized_allow_list" != *"$required"* ]]; then
    echo "FAIL: uri_allow_list missing ${required}" >&2
    fail=1
  fi
done

if [[ "$fail" -eq 1 ]]; then
  echo >&2
  echo "Remediation:" >&2
  echo "  set -a && source prod.env && set +a   # include SUPABASE_ACCESS_TOKEN" >&2
  echo "  bash scripts/supabase/ci_sync.sh sync-production" >&2
  echo "  bash scripts/supabase/verify_live_auth_urls.sh" >&2
  exit 1
fi

echo "OK: live Supabase auth URLs match EV-007 staging-first contract."
