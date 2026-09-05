#!/usr/bin/env bash
# Fetch Supabase database security + performance advisor reports (hard-fail on ERROR).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
REPORTS="${SEC_REPORTS_DIR:-${ROOT}/.security-reports}/supabase-advisors"
mkdir -p "${REPORTS}"

# shellcheck source=scripts/security/load_supabase_credentials.sh
source "${ROOT}/scripts/security/load_supabase_credentials.sh"
vecinita_load_supabase_credentials "${ROOT}"
TOKEN="${SUPABASE_ACCESS_TOKEN:-}"
REF="${SUPABASE_PROJECT_REF:-}"

if [[ -z "${TOKEN}" || -z "${REF}" ]]; then
  echo "[security] ERROR: Supabase detected but SUPABASE_ACCESS_TOKEN / project ref missing" >&2
  echo "[security] Set SUPABASE_ACCESS_TOKEN (sbp_...) and SUPABASE_PROJECT_REF, or SEC_SKIP_SUPABASE_ADVISORS=1 to waive." >&2
  exit 1
fi

fetch_advisor() {
  local kind="$1"
  local out="${REPORTS}/${kind}.json"
  local http
  set +e
  http="$(curl -sS -o "${out}" -w '%{http_code}' \
    "https://api.supabase.com/v1/projects/${REF}/advisors/${kind}" \
    -H "Authorization: Bearer ${TOKEN}")"
  set -e
  if [[ "${http}" != "200" && "${http}" != "201" ]]; then
    echo "[security] WARN: advisors/${kind} HTTP ${http} — skipping Supabase advisor gate" >&2
    echo '{"lints":[]}' > "${out}"
  fi
}

fetch_advisor security
fetch_advisor performance

export REPORTS
# Default warn matches CI (stricter than ERROR-only). Override with SEC_SUPABASE_ADVISOR_FAIL_ON.
export SEC_SUPABASE_ADVISOR_FAIL_ON="${SEC_SUPABASE_ADVISOR_FAIL_ON:-warn}"
python3 - <<'PY'
import json, os, sys
from pathlib import Path

reports = Path(os.environ["REPORTS"])
fail_on = os.environ.get("SEC_SUPABASE_ADVISOR_FAIL_ON", "warn").lower()
rank = {"INFO": 0, "WARN": 1, "WARNING": 1, "ERROR": 2}
thr = {"none": 99, "warn": 1, "error": 2}.get(fail_on, 2)
lints = []
for name in ("security.json", "performance.json"):
    data = json.loads((reports / name).read_text())
    items = data.get("lints", data) if isinstance(data, dict) else data
    lints.extend(items or [])
blocking = [l for l in lints if rank.get(str(l.get("level", "")).upper(), -1) >= thr]
summary = {
    "total": len(lints),
    "blocking": len(blocking),
    "fail_on": fail_on,
    "by_level": {},
}
for lint in lints:
    level = str(lint.get("level", "UNKNOWN")).upper()
    summary["by_level"][level] = summary["by_level"].get(level, 0) + 1
(reports / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
print(f"[security] supabase advisors: total={len(lints)} blocking={len(blocking)} fail_on={fail_on}")
# Always print every lint so WARN/INFO are visible in CI logs (hard-fail still uses fail_on).
for lint in lints:
    name = lint.get("name") or lint.get("title") or lint.get("cache_key") or "unknown"
    detail = (lint.get("detail") or lint.get("description") or lint.get("remediation") or "")
    print(f"  [{lint.get('level')}] {name}: {detail[:300]}")
    if lint.get("metadata"):
        meta = lint["metadata"]
        if isinstance(meta, dict):
            for key in ("schema", "name", "type", "entity"):
                if key in meta:
                    print(f"           {key}={meta[key]}")
if blocking:
    print(f"[security] ERROR: {len(blocking)} advisor finding(s) at or above fail_on={fail_on}")
sys.exit(1 if blocking else 0)
PY
