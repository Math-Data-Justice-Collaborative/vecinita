#!/usr/bin/env bash
# Apply live Supabase advisor remediations (idempotent).
# Prefer Management API; fall back to supabase CLI link + db/config push when available.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "${ROOT}"

# shellcheck source=scripts/security/load_supabase_credentials.sh
source "${ROOT}/scripts/security/load_supabase_credentials.sh"
vecinita_load_supabase_credentials "${ROOT}"
TOKEN="${SUPABASE_ACCESS_TOKEN:-}"
REF="${SUPABASE_PROJECT_REF:-}"

if [[ -z "${TOKEN}" || -z "${REF}" ]]; then
  echo "[security] ERROR: need SUPABASE_ACCESS_TOKEN and project ref to remediate advisors" >&2
  exit 1
fi

export SUPABASE_ACCESS_TOKEN="${TOKEN}"
export SUPABASE_PROJECT_REF="${REF}"

auth_hdr=(-H "Authorization: Bearer ${TOKEN}" -H "Content-Type: application/json")

run_sql() {
  local sql="$1"
  local payload resp http
  payload="$(python3 -c 'import json,sys; print(json.dumps({"query": sys.argv[1]}))' "${sql}")"
  set +e
  resp="$(curl -sS -w '\n%{http_code}' "https://api.supabase.com/v1/projects/${REF}/database/query" \
    "${auth_hdr[@]}" \
    -d "${payload}")"
  http="$(printf '%s' "${resp}" | tail -1)"
  body="$(printf '%s' "${resp}" | sed '$d')"
  set -e
  if [[ "${http}" != "201" && "${http}" != "200" ]]; then
    echo "[security] WARN: database/query HTTP ${http}: ${body}" >&2
    return 1
  fi
  return 0
}

echo "[security] remediating SQL: revoke PostgREST execute on public.rls_auto_enable()"
SQL_OK=0
REVOKE_SQL="DO \$\$ BEGIN IF to_regprocedure('public.rls_auto_enable()') IS NOT NULL THEN REVOKE ALL ON FUNCTION public.rls_auto_enable() FROM PUBLIC, anon, authenticated; GRANT EXECUTE ON FUNCTION public.rls_auto_enable() TO postgres, service_role; END IF; END \$\$;"
if run_sql "${REVOKE_SQL}"; then
  SQL_OK=1
  echo "[security] SQL remediation applied via Management API"
else
  echo "[security] Management API SQL failed — will try supabase CLI db push if available"
fi

echo "[security] remediating Auth config: enable TOTP MFA + percentage DB pool unit"
set +e
auth_get_http="$(curl -sS -o /tmp/supabase-auth-config.json -w '%{http_code}' \
  "https://api.supabase.com/v1/projects/${REF}/config/auth" \
  -H "Authorization: Bearer ${TOKEN}")"
set -e
if [[ "${auth_get_http}" != "200" && "${auth_get_http}" != "201" ]]; then
  # Token may lack Auth config scope (Management API 401) — do not block CI/hotfix merges.
  echo "[security] WARN: Auth config GET HTTP ${auth_get_http} — skipping Auth remediation" >&2
else
  python3 - <<'PY' > /tmp/supabase-auth-patch.json
import json
from pathlib import Path

cfg = json.loads(Path("/tmp/supabase-auth-config.json").read_text())
patch = {
    "mfa_totp_enroll_enabled": True,
    "mfa_totp_verify_enabled": True,
    "db_max_pool_size_unit": "percent",
    "db_max_pool_size": int(cfg.get("db_max_pool_size") or 10),
}
Path("/tmp/supabase-auth-patch.json").write_text(json.dumps(patch))
print(json.dumps(patch, indent=2))
PY

  set +e
  auth_resp="$(curl -sS -w '\n%{http_code}' -X PATCH "https://api.supabase.com/v1/projects/${REF}/config/auth" \
    "${auth_hdr[@]}" \
    -d @/tmp/supabase-auth-patch.json)"
  auth_http="$(printf '%s' "${auth_resp}" | tail -1)"
  auth_body="$(printf '%s' "${auth_resp}" | sed '$d')"
  set -e
  if [[ "${auth_http}" != "200" && "${auth_http}" != "201" ]]; then
    echo "[security] WARN: Auth config PATCH HTTP ${auth_http}: ${auth_body} — continuing" >&2
  else
    echo "[security] Auth config remediation applied"
  fi
fi

# If Management API SQL failed, apply the migration via supabase CLI when DB password is present.
if [[ "${SQL_OK}" -ne 1 ]]; then
  if ! command -v supabase >/dev/null 2>&1; then
    echo "[security] ERROR: supabase CLI missing and Management API SQL failed" >&2
    exit 1
  fi
  if [[ -z "${SUPABASE_DB_PASSWORD:-}" ]]; then
    echo "[security] ERROR: SUPABASE_DB_PASSWORD required for supabase db push fallback" >&2
    exit 1
  fi
  echo "[security] linking project and pushing migrations via supabase CLI"
  supabase link --project-ref "${REF}" --password "${SUPABASE_DB_PASSWORD}" --yes
  supabase db push --yes
  echo "[security] supabase db push complete"
fi

echo "[security] supabase advisor remediations complete for project ${REF}"
