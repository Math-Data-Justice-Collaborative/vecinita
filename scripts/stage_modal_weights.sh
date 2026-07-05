#!/usr/bin/env bash
# QA-003 / D6–D7: warm-download Modal volume weights and print verification steps.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
# shellcheck source=modal_ensure_workspace.sh
source "${ROOT}/scripts/modal_ensure_workspace.sh"

DEPLOY="${VECINITA_STAGE_MODAL_DEPLOY:-1}"
DEPLOY_LLM="${VECINITA_STAGE_MODAL_DEPLOY_LLM:-0}"
SKIP_LLM="${VECINITA_STAGE_SKIP_LLM:-0}"

modal token info | sed -n '1,3p'

if [[ "$DEPLOY" == "1" ]]; then
  echo "==> Deploying vecinita-embedding (set VECINITA_STAGE_MODAL_DEPLOY=0 to skip)..."
  modal deploy infra/modal/embedding_app.py
  if [[ "$DEPLOY_LLM" == "1" ]]; then
    echo "==> Deploying vecinita-llm (VECINITA_STAGE_MODAL_DEPLOY_LLM=1; needs free Web Function quota)..."
    modal deploy infra/modal/llm_app.py
  else
    echo "==> Skipping LLM deploy (default). Set VECINITA_STAGE_MODAL_DEPLOY_LLM=1 to deploy vecinita-llm."
  fi
else
  echo "==> Skipping deploy (VECINITA_STAGE_MODAL_DEPLOY=0)."
fi

echo "==> Staging D6 FastEmbed weights into volume embedding-models..."
modal run infra/modal/embedding_app.py::stage_embedding_weights

if [[ "$SKIP_LLM" == "1" ]]; then
  echo "==> Skipping D7 LLM staging (VECINITA_STAGE_SKIP_LLM=1)."
else
  echo "==> Staging D7 Qwen weights into volume llm-models (GPU; may take 15–45 min)..."
  modal run infra/modal/llm_app.py::stage_llm_weights
fi

cat <<'EOF'

==> Volume staging jobs finished.

Next: record deployed web URLs and verify live endpoints.

1. Open the Modal dashboard for apps vecinita-embedding and vecinita-llm, or use deploy output URLs.
2. Export (no trailing slash on base; paths are appended by clients):
     export VECINITA_MODAL_EMBED_URL='https://<embedding-host>'
     export VECINITA_MODAL_LLM_URL='https://<llm-host>'
3. Health checks:
     curl -fsS "$VECINITA_MODAL_EMBED_URL/health"
     curl -fsS "$VECINITA_MODAL_LLM_URL/health"
4. Embedding dimension (expect 384):
     curl -fsS -X POST "$VECINITA_MODAL_EMBED_URL/embed" \
       -H 'Content-Type: application/json' \
       -d '{"text":"staging check"}' | python3 -c "import json,sys; e=json.load(sys.stdin)['embedding']; print(len(e))"
5. Pytest smoke (optional):
     uv run pytest tests/smoke/test_modal_weights_staged.py -v

6. After successful checks, set D6/D7 to verified in docs/sessions/S000-internal-docs-archive/data-staging-state.md.

EOF
