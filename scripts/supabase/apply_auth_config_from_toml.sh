#!/usr/bin/env bash
# Push auth URL settings from supabase/config.toml to the linked cloud project.
# Requires SUPABASE_ACCESS_TOKEN (account PAT — NOT SUPABASE_SECRET_KEY).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

CONFIG="$ROOT/supabase/config.toml"
PROJECT_REF="${SUPABASE_PROJECT_REF:-cfuvghdsuwactfeamtym}"
STAGING_ADMIN_ORIGIN="https://vecinita-admin-frontend-ef4ob.ondigitalocean.app"

# shellcheck source=scripts/security/load_supabase_credentials.sh
source "${ROOT}/scripts/security/load_supabase_credentials.sh"
vecinita_load_supabase_credentials "${ROOT}"
PROJECT_REF="${SUPABASE_PROJECT_REF:-$PROJECT_REF}"

if [[ -z "${SUPABASE_ACCESS_TOKEN:-}" ]]; then
	echo "ERROR: SUPABASE_ACCESS_TOKEN is not set." >&2
	echo "  Project keys (SUPABASE_SECRET_KEY / SUPABASE_PUBLISHABLE_KEY) cannot update site_url." >&2
	echo "  Create a personal access token: https://supabase.com/dashboard/account/tokens" >&2
	exit 1
fi

if [[ ! -f "$CONFIG" ]]; then
	echo "ERROR: missing $CONFIG" >&2
	exit 1
fi

# Parse site_url + redirects and build Management API payload.
# uri_allow_list must be comma-separated — newlines are stripped by the API and
# concatenate URLs into a single invalid entry.
#
# Also pin advisor remediations that config.toml cannot express yet:
#   - mfa_totp_* from [auth.mfa.totp]
#   - db_max_pool_size_unit=percent (CLI config.toml has no field; Management API only)
payload="$(
	PROJECT_REF="${PROJECT_REF}" SUPABASE_ACCESS_TOKEN="${SUPABASE_ACCESS_TOKEN}" python3 <<'PY'
import json
import os
import re
import urllib.request
from pathlib import Path

text = Path("supabase/config.toml").read_text(encoding="utf-8")
site = re.search(r'^site_url\s*=\s*"([^"]+)"', text, re.M)
if not site:
    raise SystemExit("site_url not found in config.toml")
urls: list[str] = []
block = re.search(r"additional_redirect_urls\s*=\s*\[(.*?)\]", text, re.S)
if block:
    urls.extend(re.findall(r'"([^"]+)"', block.group(1)))

totp = re.search(
    r"\[auth\.mfa\.totp\](.*?)(?=\n\[|\Z)",
    text,
    re.S,
)
enroll = True
verify = True
if totp:
    enroll = "enroll_enabled = true" in totp.group(1)
    verify = "verify_enabled = true" in totp.group(1)

ref = os.environ["PROJECT_REF"]
token = os.environ["SUPABASE_ACCESS_TOKEN"]
req = urllib.request.Request(
    f"https://api.supabase.com/v1/projects/{ref}/config/auth",
    headers={
        "Authorization": f"Bearer {token}",
        "User-Agent": "vecinita-supabase-auth-sync/1.0",
    },
)
with urllib.request.urlopen(req, timeout=60) as resp:
    current = json.loads(resp.read().decode())
pool_size = int(current.get("db_max_pool_size") or 10)

print(
    json.dumps(
        {
            "site_url": site.group(1),
            "uri_allow_list": ",".join(urls),
            "mfa_totp_enroll_enabled": enroll,
            "mfa_totp_verify_enabled": verify,
            "db_max_pool_size_unit": "percent",
            "db_max_pool_size": pool_size,
        }
    )
)
PY
)"

site_url="$(python3 -c 'import json,sys; print(json.loads(sys.argv[1])["site_url"])' "${payload}")"
redirect_count="$(python3 -c 'import json,sys; print(len(json.loads(sys.argv[1])["uri_allow_list"].split(",")))' "${payload}")"

if [[ "$site_url" != "$STAGING_ADMIN_ORIGIN" ]]; then
	echo "ERROR: config.toml site_url must be ${STAGING_ADMIN_ORIGIN}" >&2
	exit 1
fi

echo "==> PATCH live auth config (project ${PROJECT_REF})"
echo "    site_url: ${site_url}"
echo "    uri_allow_list entries: ${redirect_count}"
echo "    mfa_totp + db_max_pool_size_unit=percent (advisor pins)"

curl -fsS -X PATCH "https://api.supabase.com/v1/projects/${PROJECT_REF}/config/auth" \
	-H "Authorization: Bearer ${SUPABASE_ACCESS_TOKEN}" \
	-H "Content-Type: application/json" \
	-H "User-Agent: vecinita-supabase-auth-sync/1.0" \
	-d "${payload}" >/dev/null

echo "==> Auth URL config patched. Running live verification..."
bash "$ROOT/scripts/supabase/verify_live_auth_urls.sh"
bash "$ROOT/scripts/supabase/check_live_invite_redirect.sh"

echo "OK: Supabase auth URLs synced from config.toml."
