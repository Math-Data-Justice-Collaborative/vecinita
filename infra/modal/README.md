# Modal apps (deploy)

| App | Module | Deploy command |
|-----|--------|----------------|
| `vecinita-embedding` | `infra/modal/embedding_app.py` | `modal deploy infra/modal/embedding_app.py` |
| `vecinita-data-management` | `infra/modal/data_management_app.py` | `modal deploy infra/modal/data_management_app.py` |
| `vecinita-llm` | `infra/modal/llm_app.py` | `modal deploy infra/modal/llm_app.py` |

## vecinita-embedding (FastEmbed)

- **Model:** `BAAI/bge-small-en-v1.5` (384-dim, ADR-008)
- **Volume:** `embedding-models` (HF cache)
- **Endpoints:** `GET /health`, `POST /embed`, `POST /embed/batch`
- **Consumer env:** `VECINITA_MODAL_EMBED_URL` on DO backends (`packages/embedding-client`)

First deploy downloads weights into the Modal volume; allow several minutes on cold start.

## vecinita-llm (vLLM)

- **Model:** `Qwen/Qwen2.5-1.5B-Instruct` (ADR-009)
- **GPU:** NVIDIA T4, `scaledown_window=300` (scale-to-zero)
- **Volume:** `llm-models` (HF cache)
- **Endpoints:** `GET /health`, `POST /generate`, `POST /generate/stream` (SSE)
- **Consumer env:** `VECINITA_MODAL_LLM_URL` on DO ChatRAG backend (`packages/llm-client`)
