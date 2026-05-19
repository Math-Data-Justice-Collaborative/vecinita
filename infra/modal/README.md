# Modal apps (deploy and local serve)

| App | Module | Deploy | Local dev (`modal serve`) |
|-----|--------|--------|---------------------------|
| `vecinita-embedding` | `embedding_app.py` | `modal deploy infra/modal/embedding_app.py` | `modal serve infra/modal/embedding_app.py` |
| `vecinita-data-management` | `data_management_app.py` | `modal deploy infra/modal/data_management_app.py` | `modal serve infra/modal/data_management_app.py` |
| `vecinita-llm` | `llm_app.py` | `modal deploy infra/modal/llm_app.py` | `modal serve infra/modal/llm_app.py` |

Run commands from the **repo root** with Modal CLI authenticated (`modal token new`).

## Local `modal serve` (F18)

Use separate terminals. After each `serve`, copy the printed URL into your env (see [docs/LOCAL_DEV.md](../../docs/LOCAL_DEV.md)).

### Embedding (CPU)

```bash
modal serve infra/modal/embedding_app.py
# → set VECINITA_MODAL_EMBED_URL to the /embed base (tunnel URL)
```

Endpoints: `GET /health`, `POST /embed`, `POST /embed/batch`

### LLM (GPU — first start downloads weights)

```bash
modal serve infra/modal/llm_app.py
# → set VECINITA_MODAL_LLM_URL to the /generate base
```

Endpoints: `GET /health`, `POST /generate`, `POST /generate/stream`

### Data management ASGI

```bash
export VECINITA_DO_WRITE_API_URL=http://localhost:8002
export VECINITA_INTERNAL_API_KEY=dev-internal-key
export VECINITA_MODAL_PROXY_KEY=dev-proxy-key
modal serve infra/modal/data_management_app.py
# → set VITE_VECINITA_ADMIN_API_URL in data-management-frontend/.env
```

Requires the **internal write API** running locally on port 8002 with `DATABASE_URL` set.

**Note:** `pytest` and most CI jobs **do not** require Modal — HTTP clients are mocked. Use `serve` when exercising real embed/LLM/GPU paths.

## Deploy (staging/production)

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
