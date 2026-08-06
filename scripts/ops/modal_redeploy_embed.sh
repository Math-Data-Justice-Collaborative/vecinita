#!/usr/bin/env bash
# Redeploy Modal embedding app (RET-002 RA-011). Default: dry-run.
# Usage:
#   scripts/ops/modal_redeploy_embed.sh           # dry-run (prints command)
#   scripts/ops/modal_redeploy_embed.sh --approve # runs after AskQuestion approval
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT"

APPROVE=0
for arg in "$@"; do
  case "$arg" in
    --approve) APPROVE=1 ;;
    --dry-run) APPROVE=0 ;;
    -h|--help)
      echo "Usage: $0 [--dry-run|--approve]"
      exit 0
      ;;
    *)
      echo "Unknown arg: $arg" >&2
      exit 2
      ;;
  esac
done

CMD=(modal deploy infra/modal/embedding_app.py)

if [[ "$APPROVE" -eq 0 ]]; then
  echo "DRY-RUN: would run: ${CMD[*]}"
  echo "Re-run with --approve only after explicit AskQuestion approval (live stack)."
  exit 0
fi

echo "==> APPROVED: ${CMD[*]}"
exec "${CMD[@]}"
