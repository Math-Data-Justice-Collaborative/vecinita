#!/usr/bin/env bash
# Stage Modal embed runtime/pin secret (RET-002 RA-011). Default: dry-run.
# Does NOT invent secret values — prints the modal secret create template.
# Usage:
#   scripts/ops/stage_embed_runtime.sh --runtime sentence_transformers
#   scripts/ops/stage_embed_runtime.sh --runtime sentence_transformers --approve
set -euo pipefail

RUNTIME=""
MODEL_ID="${VECINITA_EMBEDDING_MODEL_ID:-intfloat/multilingual-e5-small}"
SECRET_NAME="${VECINITA_EMBED_SECRET_NAME:-vecinita-embedding}"
APPROVE=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --runtime)
      RUNTIME="${2:-}"
      shift 2
      ;;
    --model-id)
      MODEL_ID="${2:-}"
      shift 2
      ;;
    --secret-name)
      SECRET_NAME="${2:-}"
      shift 2
      ;;
    --approve)
      APPROVE=1
      shift
      ;;
    --dry-run)
      APPROVE=0
      shift
      ;;
    -h|--help)
      echo "Usage: $0 --runtime fastembed|sentence_transformers|onnx [--model-id ID] [--approve]"
      exit 0
      ;;
    *)
      echo "Unknown arg: $1" >&2
      exit 2
      ;;
  esac
done

if [[ -z "$RUNTIME" ]]; then
  echo "ERROR: --runtime is required" >&2
  exit 2
fi

CMD=(
  modal secret create "$SECRET_NAME"
  "VECINITA_EMBED_RUNTIME=${RUNTIME}"
  "VECINITA_EMBEDDING_MODEL_ID=${MODEL_ID}"
  --force
)

if [[ "$APPROVE" -eq 0 ]]; then
  echo "DRY-RUN: would run:"
  printf '  %q' "${CMD[@]}"
  echo
  echo "Re-run with --approve only after explicit AskQuestion approval (live stack / ADR-049)."
  exit 0
fi

echo "==> APPROVED: modal secret create ${SECRET_NAME} (runtime=${RUNTIME})"
exec "${CMD[@]}"
