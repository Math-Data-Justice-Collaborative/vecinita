#!/usr/bin/env bash
# Push auth URL settings from supabase/config.toml to the linked cloud project.
# Requires SUPABASE_ACCESS_TOKEN (account PAT — NOT SUPABASE_SECRET_KEY).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

CONFIG="$ROOT/supabase/config.toml"
PROJECT_REF="${SUPABASE_PROJECT_REF:-cfuvghdsuwactfeamtym}"
STAGING_ADMIN_ORIGIN="https://vecinita-admin-frontend-ef4ob.ondigitalocean.app"

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

# Parse site_url and additional_redirect_urls from config.toml (offline contract source).
mapfile -t parsed < <(python3 <<'PY'
import re
from pathlib import Path

text = Path("supabase/config.toml").read_text(encoding="utf-8")
site = re.search(r'^site_url\s*=\s*"([^"]+)"', text, re.M)
if not site:
    raise SystemExit("site_url not found in config.toml")
urls: list[str] = []
block = re.search(
    r"additional_redirect_urls\s*=\s*\[(.*?)\]",
    text,
    re.S,
)
if block:
    urls.extend(re.findall(r'"([^"]+)"', block.group(1)))
print(site.group(1))
for url in urls:
    print(url)
PY
)
site_url="${parsed[0]}"
redirect_lines="$(printf '%s\n' "${parsed[@]:1}")"

if [[ "$site_url" != "$STAGING_ADMIN_ORIGIN" ]]; then
  echo "ERROR: config.toml site_url must be ${STAGING_ADMIN_ORIGIN}" >&2
  exit 1
fi

echo "==> PATCH live auth config (project ${PROJECT_REF})"
echo "    site_url: ${site_url}"
echo "    uri_allow_list entries: $(printf '%s\n' "$redirect_lines" | sed '/^$/d' | wc -l)"

payload="$(SITE_URL="$site_url" REDIRECT_LINES="$redirect_lines" python3 <<'PY'
import json
import os

redirects = [line for line in os.environ["REDIRECT_LINES"].splitlines() if line.strip()]
print(json.dumps({"site_url": os.environ["SITE_URL"], "uri_allow_list": "\n".join(redirects)}))
PY
)"

curl -fsS -X PATCH "https://api.supabase.com/v1/projects/${PROJECT_REF}/config/auth" \
  -H "Authorization: Bearer ${SUPABASE_ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d "$payload" >/dev/null

echo "==> Auth URL config patched. Running live verification..."
bash "$ROOT/scripts/supabase/verify_live_auth_urls.sh"
bash "$ROOT/scripts/supabase/check_live_invite_redirect.sh"

echo "OK: Supabase auth URLs synced from config.toml."
