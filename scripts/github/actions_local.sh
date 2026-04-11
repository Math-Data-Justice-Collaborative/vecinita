#!/usr/bin/env bash
# Dispatcher for `make actions-local`:
# - Default: run local parity (no Docker/act) via run_actions_local_make.sh
# - USE_ACT=1: use nektos/act when installed; otherwise fall back to parity with a notice.

set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ "${USE_ACT:-}" == "1" ]]; then
	if command -v act >/dev/null 2>&1; then
		exec "${HERE}/run_act_workflows.sh" "$@"
	else
		echo "USE_ACT=1 but act is not installed; running make-based parity instead." >&2
		echo "Install act: https://github.com/nektos/act#installation" >&2
	fi
fi

exec "${HERE}/run_actions_local_make.sh" "$@"
