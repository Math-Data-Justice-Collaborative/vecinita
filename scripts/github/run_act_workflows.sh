#!/usr/bin/env bash
# Run GitHub Actions workflow files locally with nektos/act (Docker required).
# Skips workflows that act cannot trigger meaningfully (reusable-only, workflow_run-only).
#
# Usage:
#   ./scripts/github/run_act_workflows.sh [extra args passed to each act invocation]
#   WORKFLOW=test.yml ./scripts/github/run_act_workflows.sh
#   ACT_EVENT=push WORKFLOW=env-sync-contract.yml ./scripts/github/run_act_workflows.sh
#
# Environment:
#   WORKFLOW          If set (e.g. test.yml), only this file under .github/workflows/ is run.
#   ACT_EVENT         Event name (default: workflow_dispatch). Use push if a file has no workflow_dispatch.
#   ACT_RUNNER_IMAGE  If set, maps ubuntu-22.04 and ubuntu-latest to this image (-P).
#   ACT_SKIP          Comma-separated basenames to skip (e.g. test.yml,modal-deploy.yml).

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

if ! command -v act >/dev/null 2>&1; then
	echo "error: act is not installed." >&2
	echo "Install nektos/act (Docker required): https://github.com/nektos/act#installation (use act >= 0.2.86)." >&2
	echo "Or run workflow parity without act: make actions-local   (see scripts/github/run_actions_local_make.sh)" >&2
	exit 1
fi

EVENT="${ACT_EVENT:-workflow_dispatch}"

RUNNER_EXTRA=()
if [[ -n "${ACT_RUNNER_IMAGE:-}" ]]; then
	RUNNER_EXTRA+=(-P "ubuntu-22.04=${ACT_RUNNER_IMAGE}" -P "ubuntu-latest=${ACT_RUNNER_IMAGE}")
fi

# workflow_call-only; workflow_run-only (no workflow_dispatch)
SKIP_ALWAYS=(
	reusable-dispatch-repo-workflow.yml
	render-post-deploy.yml
)

IFS=',' read -ra USER_SKIPS <<< "${ACT_SKIP:-}"

skip_always() {
	local b="$1"
	local s
	for s in "${SKIP_ALWAYS[@]}"; do
		[[ "$b" == "$s" ]] && return 0
	done
	return 1
}

skip_user() {
	local b="$1"
	local s
	for s in "${USER_SKIPS[@]}"; do
		[[ -n "$s" ]] || continue
		[[ "$b" == "$s" ]] && return 0
	done
	return 1
}

should_run() {
	local b="$1"
	skip_always "$b" && return 1
	skip_user "$b" && return 1
	return 0
}

run_one() {
	local wf=$1
	shift
	# shellcheck disable=SC2068
	act "${EVENT}" -W "${wf}" "${RUNNER_EXTRA[@]}" "$@"
}

if [[ -n "${WORKFLOW:-}" ]]; then
	wf=".github/workflows/${WORKFLOW}"
	if [[ ! -f "${wf}" ]]; then
		echo "error: workflow not found: ${wf}" >&2
		exit 1
	fi
	echo "act ${EVENT} -W ${wf} $*"
	run_one "${wf}" "$@"
	exit 0
fi

failed=0
shopt -s nullglob
for wf in .github/workflows/*.yml; do
	base="$(basename "${wf}")"
	if ! should_run "${base}"; then
		echo "[skip] ${base}"
		continue
	fi
	echo ""
	echo "========== act ${EVENT}: ${base} =========="
	if ! run_one "${wf}" "$@"; then
		echo "FAILED: ${base}" >&2
		failed=1
	fi
done

exit "${failed}"
