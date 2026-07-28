#!/usr/bin/env bash
# Fetch Supabase database security + performance advisor reports (hard-fail on ERROR).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
REPORTS="${SEC_REPORTS_DIR:-${ROOT}/.security-reports}/supabase-advisors"
mkdir -p "${REPORTS}"

# Parse-only from .env / prod.env — do not source.
load_env_key() {
  local key="$1" file="$2"
  [[ -f "${file}" ]] || return 0
  local line
  line="$(grep -E "^${key}=" "${file}" | tail -1 || true)"
  [[ -n "${line}" ]] || return 0
  printf '%s' "${line#*=}" | sed 's/^["'\'']//; s/["'\'']$//'
}

TOKEN="${SUPABASE_ACCESS_TOKEN:-}"
REF="${SUPABASE_PROJECT_REF:-}"

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
  REF="$(load_env_key SUPABASE_PROJECT_REF "${ROOT}/prod.env")"
fi
if [[ -z "${REF}" ]]; then
  REF="$(load_env_key SUPABASE_PROJECT_ID "${ROOT}/.env")"
fi
if [[ -z "${REF}" ]]; then
  REF="$(load_env_key SUPABASE_PROJECT_ID "${ROOT}/prod.env")"
fi
if [[ -z "${REF}" && -f "${ROOT}/supabase/config.toml" ]]; then
  REF="$(sed -n 's/^project_id[[:space:]]*=[[:space:]]*"\([^"]*\)".*/\1/p' "${ROOT}/supabase/config.toml" | head -1)"
fi

if [[ -z "${TOKEN}" || -z "${REF}" ]]; then
  echo "[security] ERROR: Supabase detected but SUPABASE_ACCESS_TOKEN / project ref missing" >&2
  echo "[security] Set SUPABASE_ACCESS_TOKEN (sbp_...) and SUPABASE_PROJECT_REF, or SEC_SKIP_SUPABASE_ADVISORS=1 to waive." >&2
  exit 1
fi

curl -fsS "https://api.supabase.com/v1/projects/${REF}/advisors/security" \
  -H "Authorization: Bearer ${TOKEN}" -o "${REPORTS}/security.json"
curl -fsS "https://api.supabase.com/v1/projects/${REF}/advisors/performance" \
  -H "Authorization: Bearer ${TOKEN}" -o "${REPORTS}/performance.json"

export REPORTS
export SEC_SUPABASE_ADVISOR_FAIL_ON="${SEC_SUPABASE_ADVISOR_FAIL_ON:-error}"
python3 - <<'PY'
import json, os, sys
from pathlib import Path

reports = Path(os.environ["REPORTS"])
fail_on = os.environ.get("SEC_SUPABASE_ADVISOR_FAIL_ON", "error").lower()
rank = {"INFO": 0, "WARN": 1, "WARNING": 1, "ERROR": 2}
thr = {"none": 99, "warn": 1, "error": 2}.get(fail_on, 2)
lints = []
for name in ("security.json", "performance.json"):
    data = json.loads((reports / name).read_text())
    items = data.get("lints", data) if isinstance(data, dict) else data
    lints.extend(items or [])
blocking = [l for l in lints if rank.get(str(l.get("level", "")).upper(), -1) >= thr]
summary = {"total": len(lints), "blocking": len(blocking), "fail_on": fail_on}
(reports / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
print(f"[security] supabase advisors: total={len(lints)} blocking={len(blocking)} fail_on={fail_on}")
if blocking:
    for lint in blocking[:20]:
        print(
            f"  [{lint.get('level')}] {lint.get('name') or lint.get('title')}: "
            f"{(lint.get('detail') or lint.get('description') or '')[:160]}"
        )
sys.exit(1 if blocking else 0)
PY
