#!/usr/bin/env bash
# Apply live Supabase advisor remediations via Management API (idempotent).
# Requires SUPABASE_ACCESS_TOKEN + project ref (SUPABASE_PROJECT_REF / config.toml).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

load_env_key() {
  local key="$1" file="$2"
  [[ -f "${file}" ]] || return 0
  local line
  line="$(grep -E "^${key}=" "${file}" | tail -1 || true)"
  [[ -n "${line}" ]] || return 0
  printf '%s' "${line#*=}" | sed 's/^["'\'']//; s/["'\'']$//'
}

TOKEN="${SUPABASE_ACCESS_TOKEN:-}"
REF="${SUPABASE_PROJECT_REF:-${SUPABASE_PROJECT_ID:-}}"
if [[ -z "${TOKEN}" ]]; then
  TOKEN="$(load_env_key SUPABASE_ACCESS_TOKEN "${ROOT}/.env")"
fi
if [[ -z "${TOKEN}" ]]; then
  TOKEN="$(load_env_key SUPABASE_ACCESS_TOKEN "${ROOT}/prod.env")"
fi
if [[ -z "${REF}" ]]; then
  REF="$(load_env_key SUPABASE_PROJECT_REF "${ROOT}/.env")"
fi
if [[ -z "${REF}" ]]; then
  REF="$(load_env_key SUPABASE_PROJECT_ID "${ROOT}/prod.env")"
fi
if [[ -z "${REF}" && -f "${ROOT}/supabase/config.toml" ]]; then
  REF="$(sed -n 's/^project_id[[:space:]]*=[[:space:]]*"\([^"]*\)".*/\1/p' "${ROOT}/supabase/config.toml" | head -1)"
fi

if [[ -z "${TOKEN}" || -z "${REF}" ]]; then
  echo "[security] ERROR: need SUPABASE_ACCESS_TOKEN and project ref to remediate advisors" >&2
  exit 1
fi

auth_hdr=(-H "Authorization: Bearer ${TOKEN}" -H "Content-Type: application/json")

echo "[security] remediating SQL: drop public.rls_auto_enable() if present"
SQL=$(
  cat <<'SQL'
DO $$
BEGIN
  IF to_regprocedure('public.rls_auto_enable()') IS NOT NULL THEN
    REVOKE ALL ON FUNCTION public.rls_auto_enable() FROM PUBLIC, anon, authenticated;
    DROP FUNCTION public.rls_auto_enable();
  END IF;
END
$$;
SQL
)
python3 -c 'import json,sys; print(json.dumps({"query": sys.stdin.read()}))' <<<"${SQL}" \
  | curl -fsS "https://api.supabase.com/v1/projects/${REF}/database/query" \
    "${auth_hdr[@]}" \
    -d @- \
  >/dev/null
echo "[security] SQL remediation applied"

echo "[security] remediating Auth config: enable TOTP MFA + percentage DB pool unit"
# GET current auth config, then PATCH only the fields we need to change.
curl -fsS "https://api.supabase.com/v1/projects/${REF}/config/auth" \
  -H "Authorization: Bearer ${TOKEN}" \
  -o /tmp/supabase-auth-config.json

python3 - <<'PY' > /tmp/supabase-auth-patch.json
import json
from pathlib import Path

cfg = json.loads(Path("/tmp/supabase-auth-config.json").read_text())
patch = {
    "mfa_totp_enroll_enabled": True,
    "mfa_totp_verify_enabled": True,
}
# Clear auth_db_connections_absolute INFO when unit supports percentage.
if "db_max_pool_size_unit" in cfg or True:
    patch["db_max_pool_size_unit"] = "percent"
    # Keep a conservative share of DB connections for Auth (10% ≈ prior absolute 10 on small).
    if not cfg.get("db_max_pool_size"):
        patch["db_max_pool_size"] = 10
    else:
        # If previously absolute "10 connections", reinterpret as 10 percent.
        patch["db_max_pool_size"] = int(cfg.get("db_max_pool_size") or 10)
Path("/tmp/supabase-auth-patch.json").write_text(json.dumps(patch) + "\n")
print(json.dumps(patch, indent=2))
PY

curl -fsS -X PATCH "https://api.supabase.com/v1/projects/${REF}/config/auth" \
  "${auth_hdr[@]}" \
  -d @/tmp/supabase-auth-patch.json \
  >/dev/null
echo "[security] Auth config remediation applied"
echo "[security] supabase advisor remediations complete for project ${REF}"
