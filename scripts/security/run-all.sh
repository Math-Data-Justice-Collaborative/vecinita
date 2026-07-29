#!/usr/bin/env bash
# Repo security suite — hard-fail. Run from repository root (or pass ROOT).
# Tools: OpenGrep, 2ms, KICS, SBOM Tool, Grype, Supabase advisors (when configured).
set -euo pipefail

ROOT="$(cd "${1:-$(pwd)}" && pwd)"
cd "${ROOT}"

PREFIX="${SEC_TOOLS_DIR:-${ROOT}/.tools/security}"
BIN_DIR="${PREFIX}/bin"
ASSETS_DIR="${PREFIX}/assets"
REPORTS="${SEC_REPORTS_DIR:-${ROOT}/.security-reports}"
CONFIG_DIR="${ROOT}/config/security"
export PATH="${BIN_DIR}:${PATH}"
export REPORTS
export SEC_TOOLS_DIR="${PREFIX}"

log() { printf '[security] %s\n' "$*"; }
err() { printf '[security] ERROR: %s\n' "$*" >&2; }

mkdir -p "${REPORTS}"

if [[ "${SEC_INSTALL:-1}" == "1" ]]; then
  bash "${ROOT}/scripts/security/install-tools.sh"
fi

need() { command -v "$1" >/dev/null 2>&1 || { err "missing $1 — run scripts/security/install-tools.sh"; exit 1; }; }

# Avoid set -e abort when SEC_FAIL_FAST=0 and the last command in run() is a
# failed `[[ ... ]] && exit` (function would return non-zero).
run() {
  local name="$1"; shift
  log "=== ${name} ==="
  set +e
  "$@"
  local c=$?
  set -e
  if [[ $c -ne 0 ]]; then
    err "${name} FAILED (exit ${c})"
    fail=1
    if [[ "${SEC_FAIL_FAST:-1}" == "1" ]]; then
      exit "$c"
    fi
  fi
  return 0
}

fail=0

need opengrep
need 2ms
need kics
need grype
need sbom-tool

# Community rule pack + optional local config (path ignores / future custom rules).
OPENGREP_ARGS=(
  scan --error --severity=ERROR
  --config=p/default
  --exclude=vendor --exclude=node_modules --exclude=.tools --exclude=.venv
  --exclude=.security-reports --exclude=coverage --exclude=htmlcov
  --json --json-output="${REPORTS}/opengrep.json"
)
if [[ -f "${CONFIG_DIR}/opengrep.yml" ]]; then
  OPENGREP_ARGS+=(--config="${CONFIG_DIR}/opengrep.yml")
fi
run OpenGrep opengrep "${OPENGREP_ARGS[@]}" "${ROOT}"
# shellcheck disable=SC2086
# Ignore gitignored local secret files (2ms has no --exclude-gitignore).
# Secrets in tracked paths still hard-fail. Complementary: gitleaks in ci-guards.
run 2ms 2ms filesystem --path "${ROOT}" \
  --report-path "${REPORTS}/2ms.json" --report-path "${REPORTS}/2ms.sarif" \
  --max-target-megabytes 50 \
  --ignore-pattern '__pycache__' \
  --ignore-pattern 'node_modules' \
  --ignore-pattern '.git' \
  --ignore-pattern '.venv' \
  --ignore-pattern '.tools' \
  --ignore-pattern '.security-reports' \
  --ignore-pattern 'coverage' \
  --ignore-pattern 'htmlcov' \
  --ignore-pattern 'dist' \
  --ignore-pattern '.pytest_cache' \
  --ignore-pattern '.ruff_cache' \
  --ignore-pattern '.env' \
  --ignore-pattern '*.env' \
  --ignore-pattern 'prod.env' \
  --ignore-pattern '.deploy-keys.local' \
  --ignore-pattern 'admin-fe-spec.yaml' \
  --ignore-pattern 'internal-write-api-spec.yaml' \
  --ignore-pattern 'chat-rag-spec.yaml' \
  --allowed-values 'vecinita.eval.explore.v1' \
  --allowed-values 'Qwen2.5-Instruct'

QUERIES="${ASSETS_DIR}/kics/assets/queries"
[[ -d "${QUERIES}" ]] || { err "KICS queries missing"; exit 1; }
mkdir -p "${REPORTS}/kics"
KICS_EXCLUDE_QUERIES=""
if [[ -f "${CONFIG_DIR}/kics-exclude-queries.txt" ]]; then
  # shellcheck disable=SC2002
  KICS_EXCLUDE_QUERIES="$(
    grep -vE '^\s*(#|$)' "${CONFIG_DIR}/kics-exclude-queries.txt" | paste -sd, -
  )"
fi
KICS_ARGS=(
  scan -p "${ROOT}" -q "${QUERIES}" -o "${REPORTS}/kics"
  --report-formats json,sarif --output-name results
  --fail-on "${SEC_KICS_FAIL_ON:-medium,high,critical}"
  --exclude-paths ".git,.tools,.security-reports,.venv,node_modules,vendor,coverage,htmlcov,dist"
  --exclude-gitignore
)
if [[ -n "${KICS_EXCLUDE_QUERIES}" ]]; then
  KICS_ARGS+=(--exclude-queries "${KICS_EXCLUDE_QUERIES}")
fi
run KICS kics "${KICS_ARGS[@]}"

if [[ "${SEC_SKIP_SBOM:-0}" != "1" ]]; then
  DROP="${REPORTS}/sbom-drop"
  MOUT="${REPORTS}/sbom"
  rm -rf "${DROP}" "${MOUT}"
  mkdir -p "${DROP}" "${MOUT}"
  # Without -li/-pm, Microsoft sbom-tool leaves every package license as NOASSERTION
  # (component-detection does not emit licenses). -li queries ClearlyDefined; -pm
  # parses package metadata. Disable with SEC_SBOM_FETCH_LICENSES=0 when offline.
  SBOM_ARGS=(
    generate -b "${DROP}" -bc "${ROOT}" -m "${MOUT}"
    -pn "${SEC_SBOM_PACKAGE_NAME:-vecinita}" -pv "${SEC_SBOM_PACKAGE_VERSION:-0.0.0}"
    -ps "${SEC_SBOM_PACKAGE_SUPPLIER:-CogniChem}"
    -nsb "${SEC_SBOM_NAMESPACE:-https://github.com/Math-Data-Justice-Collaborative/vecinita}"
    -D true
  )
  if [[ "${SEC_SBOM_FETCH_LICENSES:-1}" == "1" ]]; then
    SBOM_ARGS+=(
      -li true
      -pm true
      -lto "${SEC_SBOM_LICENSE_TIMEOUT_SEC:-300}"
    )
  fi
  run SBOM sbom-tool "${SBOM_ARGS[@]}"

  SPDX_CANDIDATE="$(find "${MOUT}" -type f -name '*.spdx.json' 2>/dev/null | head -1 || true)"
  if [[ -n "${SPDX_CANDIDATE}" && "${SEC_SBOM_ENRICH_LICENSES:-1}" == "1" ]]; then
    # ClearlyDefined bulk (-li) often 524s; fill licenses from npm/PyPI registries.
    # Also emit python-licenses.json from uv.lock (UvLock detections are dropped from SPDX).
    ENRICH_ARGS=(
      "${ROOT}/scripts/security/enrich_sbom_licenses.py"
      --spdx "${SPDX_CANDIDATE}"
      --summary "${REPORTS}/sbom-license-enrichment.json"
    )
    if [[ -f "${ROOT}/uv.lock" ]]; then
      ENRICH_ARGS+=(
        --uv-lock "${ROOT}/uv.lock"
        --uv-out "${REPORTS}/sbom/python-licenses.json"
      )
    fi
    run "SBOM license enrich" python3 "${ENRICH_ARGS[@]}"
  fi
fi

SPDX="$(find "${REPORTS}/sbom" -type f -name '*.spdx.json' 2>/dev/null | head -1 || true)"
if [[ -n "${SPDX}" ]]; then
  TARGET="sbom:${SPDX}"
else
  TARGET="dir:${ROOT}"
fi

GRYPE_IGNORE=()
if [[ -f "${CONFIG_DIR}/grype-ignore.yaml" ]]; then
  GRYPE_IGNORE=(--config "${CONFIG_DIR}/grype-ignore.yaml")
fi
run Grype grype "${TARGET}" --fail-on "${SEC_GRYPE_FAIL_ON:-high}" -o json \
  --file "${REPORTS}/grype.json" \
  --exclude=node_modules --exclude=vendor --exclude=.git --exclude=.venv \
  --exclude=.tools --exclude=.security-reports \
  "${GRYPE_IGNORE[@]}"

# Supabase advisors when detected
if [[ -f "${ROOT}/supabase/config.toml" || -n "${SUPABASE_PROJECT_REF:-}" || -n "${SUPABASE_URL:-}" ]]; then
  if [[ "${SEC_SKIP_SUPABASE_ADVISORS:-0}" == "1" ]]; then
    log "skipping Supabase advisors (SEC_SKIP_SUPABASE_ADVISORS=1)"
  else
    run "Supabase advisors" bash "${ROOT}/scripts/security/run-supabase-advisors.sh"
  fi
fi

if [[ "${fail}" -ne 0 ]]; then
  err "security suite failed — see ${REPORTS}"
  exit 1
fi
log "security suite passed — ${REPORTS}"
