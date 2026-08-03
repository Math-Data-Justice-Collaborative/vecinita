#!/usr/bin/env bash
# Husky pre-commit — heavier local gates offloaded from push (F62 / #182 / S025-D5).
#
# Runs: typecheck + security-scan + job_type dispatch (BUG-2026-07-31).
# Format-check stays PR / make ci-push only.
# Skip: VECINITA_SKIP_PRE_COMMIT=1 git commit
set -euo pipefail

if [[ "${VECINITA_SKIP_PRE_COMMIT:-}" == "1" ]]; then
	echo "pre-commit: skipped (VECINITA_SKIP_PRE_COMMIT=1)"
	exit 0
fi

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

echo "pre-commit: make typecheck"
make typecheck

echo "pre-commit: make security-scan"
# Load SUPABASE_ACCESS_TOKEN / PROJECT_REF from .env or prod.env (parse-only) so
# local commits exercise advisors the same way CI does when the token is present.
# shellcheck source=scripts/security/load_supabase_credentials.sh
source "${ROOT}/scripts/security/load_supabase_credentials.sh"
vecinita_load_supabase_credentials "${ROOT}"
if [[ -z "${SUPABASE_ACCESS_TOKEN:-}" && "${SEC_SKIP_SUPABASE_ADVISORS:-}" != "1" ]]; then
	echo "pre-commit: no SUPABASE_ACCESS_TOKEN in env/.env/prod.env — skipping Supabase advisors (set token or SEC_SKIP_SUPABASE_ADVISORS=1)"
	export SEC_SKIP_SUPABASE_ADVISORS=1
elif [[ "${SEC_SKIP_SUPABASE_ADVISORS:-}" != "1" ]]; then
	echo "pre-commit: Supabase advisors enabled (token present; ref=${SUPABASE_PROJECT_REF:-unset})"
fi
make security-scan

# Job dispatch gate (may also honor VECINITA_SKIP_PRE_COMMIT — already handled above)
bash "${ROOT}/scripts/ci/pre_commit_job_dispatch.sh"
