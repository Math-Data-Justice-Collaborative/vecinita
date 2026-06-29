# Modal apps (deploy and local serve)

| App | Module | Deploy | Local dev (`modal serve`) |
|-----|--------|--------|---------------------------|
| `vecinita-embedding` | `embedding_app.py` | `modal deploy infra/modal/embedding_app.py` | `modal serve infra/modal/embedding_app.py` |
| `vecinita-data-management` | `data_management_app.py` | `modal deploy infra/modal/data_management_app.py` | `modal serve infra/modal/data_management_app.py` |
| `vecinita-llm` | `llm_app.py` | `modal deploy infra/modal/llm_app.py` | `modal serve infra/modal/llm_app.py` |

Run commands from the **repo root** with Modal CLI authenticated (`modal token new`).

## Workspace (required)

All Vecinita Modal apps must deploy to the **`vecinita`** workspace — not `fontface` or other profiles.

```bash
modal profile activate vecinita
# or rely on deploy scripts (they call scripts/modal_ensure_workspace.sh):
bash scripts/deploy/modal.sh
```

Deployed URLs use the workspace prefix, e.g.  
`https://vecinita--vecinita-embedding-embedding-api.modal.run`

To retire mistaken deploys on another workspace:

```bash
modal profile activate fontface
modal app stop vecinita-embedding
modal app stop vecinita-llm
modal profile activate vecinita
```

## Local `modal serve` (F18)

Use separate terminals. After each `serve`, copy the printed URL into your env (see [docs/LOCAL_DEV.md](../../docs/LOCAL_DEV.md)).

### Embedding (CPU)

```bash
modal serve infra/modal/embedding_app.py
# → set VECINITA_MODAL_EMBED_URL to the ASGI base URL from deploy output
#   (e.g. https://<workspace>--vecinita-embedding-embedding-api.modal.run)
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
export VECINITA_INTERNAL_WRITE_URL=http://localhost:8002
export VECINITA_INTERNAL_API_KEY=dev-internal-key
export VECINITA_MODAL_PROXY_KEY=dev-proxy-key
modal serve infra/modal/data_management_app.py
# → set VITE_VECINITA_ADMIN_API_URL in data-management-frontend/.env
```

Requires the **internal write API** running locally on port 8002 with `DATABASE_URL` set.

**Note:** `pytest` and most CI jobs **do not** require Modal — HTTP clients are mocked. Use `serve` when exercising real embed/LLM/GPU paths.


## Staging model weights (D6 / D7)

Before marking FastEmbed or Qwen assets **verified** in `docs/data-staging-state.md`, populate Modal volumes:

```bash
./scripts/stage_modal_weights.sh
```

This deploys embed/LLM apps (by default), runs one-shot `stage_embedding_weights` / `stage_llm_weights` jobs, and prints curl/pytest verification steps. Live smoke: `tests/smoke/test_modal_weights_staged.py` with `VECINITA_MODAL_EMBED_URL` and `VECINITA_MODAL_LLM_URL`.

## Deploy (staging/production)

Use `bash scripts/deploy/modal.sh` (enforces **vecinita** workspace).

**Continuous deployment:** `.github/workflows/deploy-modal.yml` runs this script automatically
after **CI** passes on `main` (see [Modal CD guide](https://modal.com/docs/guide/continuous-deployment)).
It authenticates via repo secrets `MODAL_TOKEN_ID` / `MODAL_TOKEN_SECRET` (token auth — no named
profile needed; `scripts/modal_ensure_workspace.sh` verifies the workspace from `modal token info`).
Manual redeploy: trigger the **Deploy Modal** workflow via `workflow_dispatch`.

**Secret (data-management):** Create `vecinita-data-management` in the [vecinita workspace](https://modal.com/secrets/vecinita/main) using **[`.env.example`](.env.example)** as the key checklist:

- `VECINITA_MODAL_EMBED_URL`, `VECINITA_INTERNAL_WRITE_URL`, `VECINITA_INTERNAL_API_KEY`
- `VECINITA_MODAL_PROXY_KEY`, `VECINITA_CORS_ORIGINS`, `VECINITA_MODAL_LLM_URL`
- `SUPABASE_URL`, `VECINITA_AUTH_REQUIRED` (EV-005 F34 — JWT on `/jobs*`)

```bash
set -a && source prod.env && set +a
modal profile activate vecinita

# Helper script (lists keys on dry run, writes with --apply):
bash scripts/deploy/sync_modal_secret.sh --apply

# Or the raw CLI equivalent:
modal secret create --force vecinita-data-management \
  VECINITA_MODAL_EMBED_URL="$VECINITA_MODAL_EMBED_URL" \
  VECINITA_INTERNAL_WRITE_URL="$VECINITA_INTERNAL_WRITE_URL" \
  VECINITA_INTERNAL_API_KEY="$VECINITA_INTERNAL_API_KEY" \
  VECINITA_MODAL_PROXY_KEY="$VECINITA_MODAL_PROXY_KEY" \
  VECINITA_CORS_ORIGINS="$VECINITA_CORS_ORIGINS" \
  VECINITA_MODAL_LLM_URL="$VECINITA_MODAL_LLM_URL" \
  SUPABASE_URL="$SUPABASE_URL" \
  VECINITA_AUTH_REQUIRED="${VECINITA_AUTH_REQUIRED:-true}"
```

If `VECINITA_CORS_ORIGINS` is omitted, the app falls back to staging DO origins baked into `create_app()`.

**Proxy key parity (H5):** `VECINITA_MODAL_PROXY_KEY` must equal DigitalOcean `VITE_VECINITA_MODAL_PROXY_KEY` on `vecinita-admin-frontend` (build-time). After any change, rebuild the admin frontend. Check with `bash scripts/deploy/check_proxy_key_parity.sh` when both values are exported in your shell.

## vecinita-embedding (FastEmbed)

- **Model:** `BAAI/bge-small-en-v1.5` (384-dim, ADR-008)
- **Volume:** `embedding-models` (HF cache)
- **Endpoints:** `GET /health`, `POST /embed`, `POST /embed/batch`
- **Consumer env:** `VECINITA_MODAL_EMBED_URL` on DO backends (`packages/embedding-client`)

First deploy downloads weights into the Modal volume; allow several minutes on cold start.

**Staging:** `./scripts/stage_modal_weights.sh` (see `docs/data-staging-state.md`).

## vecinita-llm (vLLM)

- **Model:** `Qwen/Qwen2.5-1.5B-Instruct` (ADR-009)
- **GPU:** NVIDIA T4, `scaledown_window=300` (scale-to-zero)
- **Volume:** `llm-models` (HF cache)
- **Endpoints:** `GET /health`, `POST /generate`, `POST /generate/stream` (SSE)
- **Consumer env:** `VECINITA_MODAL_LLM_URL` on DO ChatRAG backend (`packages/llm-client`)
