# Modal apps (deploy and local serve)

| App | Module | Deploy | Local dev (`modal serve`) |
|-----|--------|--------|---------------------------|
| `vecinita-embedding` | `embedding_app.py` | `modal deploy infra/modal/embedding_app.py` | `modal serve infra/modal/embedding_app.py` |
| `vecinita-data-management` | `data_management_app.py` | `modal deploy infra/modal/data_management_app.py` | `modal serve infra/modal/data_management_app.py` |
| `vecinita-llm` | `llm_app.py` | `modal deploy infra/modal/llm_app.py` | `modal serve infra/modal/llm_app.py` |
| `vecinita-llm-playground` | `llm_playground_app.py` | `modal deploy infra/modal/llm_playground_app.py` | `modal serve infra/modal/llm_playground_app.py` |
| `vecinita-llm-finetune` | `finetune_app.py` | `modal deploy infra/modal/finetune_app.py` | Volume `llm-finetune-adapters`; pins: `finetune_pins.py` (ADR-053 / F77) |

Run commands from the **repo root** with Modal CLI authenticated (`modal token new`).

## Workspace + Environment (required)

| Role | Modal workspace | Modal Environment | Web URL source prefix |
|------|-----------------|-------------------|------------------------|
| **prod** | **`vecinita`** | **`main`** (default) | `vecinita--` |
| **staging** | **`vecinita`** | **`staging`** (web suffix `staging`) | `vecinita-staging--` |

One workspace, two [Environments](https://modal.com/docs/guide/environments) (ADR-054 / F83).
Same App names; secrets and volumes are Environment-scoped.

```bash
# Prod (Environment main)
export VECINITA_MODAL_WORKSPACE=vecinita
export MODAL_ENVIRONMENT=main   # or leave unset
bash scripts/deploy/modal.sh

# Staging
export VECINITA_MODAL_WORKSPACE=vecinita
export MODAL_ENVIRONMENT=staging
# One-time: modal environment create staging
#           modal environment update staging --set-web-suffix staging
bash scripts/deploy/modal.sh
```

Deployed URLs:
`https://vecinita--vecinita-embedding-embedding-api.modal.run` (prod) vs  
`https://vecinita-staging--vecinita-embedding-embedding-api.modal.run` (staging env suffix).

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

### LLM — prod (`vecinita-llm`, GPU — first start downloads weights)

```bash
modal serve infra/modal/llm_app.py
# → set VECINITA_MODAL_LLM_URL to the ASGI base URL (no trailing slash)
```

**Prod surface (ADR-037):** ChatRAG / ingest inference on pinned Qwen. Optional promoted LoRA
adapter after human promote (`VECINITA_FINETUNE_ADAPTER_ID`). `vecinita-ollama` is deprecated —
do not deploy.

| Route | Auth | Purpose |
|-------|------|---------|
| `GET /health` | — | Liveness |
| `POST /warm` | proxy key | Preload default or `{"model_id": …}` into VRAM |
| `POST /generate` | proxy key | Completion |
| `POST /generate/stream` | proxy key | SSE token stream |

### LLM — playground (`vecinita-llm-playground`)

```bash
modal serve infra/modal/llm_playground_app.py
# → set VECINITA_MODAL_LLM_PLAYGROUND_URL (admin / eval sandbox only — never ChatRAG)
```

List/pull and sandbox eval use the playground URL. Path aliases `GET/POST /models/ollama`
remain for FE compat.

**Modal one-shot staging functions** (prod app module):

```bash
modal run infra/modal/llm_app.py::stage_llm_weights      # default Qwen2.5-1.5B via vLLM warmup
modal run infra/modal/llm_app.py::stage_default_model    # playground default tag (HF Hub)
modal run infra/modal/llm_app.py::pull_model_job --job-id test --model-id qwen3:8b
```

### Data management ASGI + automations

```bash
export VECINITA_INTERNAL_WRITE_URL=http://localhost:8002
export VECINITA_INTERNAL_API_KEY=dev-internal-key
export VECINITA_MODAL_PROXY_KEY=dev-proxy-key
modal serve infra/modal/data_management_app.py
# → set VITE_VECINITA_ADMIN_API_URL in data-management-frontend/.env
```

Requires the **internal write API** running locally on port 8002 with `DATABASE_URL` set.

**Shared schedule (corpus automations):** one daily Modal schedule runs catch-up
(`job_type=automation_catchup`) and freshness (`job_type=freshness_refresh`). Catch-up is
residual failed/partial/missing embeds only. Freshness default stale threshold is 30 days
(`VECINITA_FRESHNESS_STALE_DAYS`). Kill-switch: `VECINITA_AUTOMATIONS_KILL_SWITCH`
(ADR-052; feature-list §F75–F76).

### LoRA fine-tune (`vecinita-llm-finetune`, F77 / ADR-053)

```bash
modal serve infra/modal/finetune_app.py
# Modal secret: vecinita-llm-finetune (see docs/staging-secrets-matrix.md §EV-027)
```

App `vecinita-llm-finetune` mounts volume **`llm-finetune-adapters`** (adapters) and shared
**`llm-models`** (pinned Qwen base). Image pins: `FINETUNE_IMAGE_PIPS` in `finetune_pins.py`.
Manual train approve; human promote only — never auto-load latest adapter on prod
(`VECINITA_FINETUNE_ADAPTER_ID` on `vecinita-llm` after promote). Train worker lands in
later M129 tasks — scaffold exposes `health()` only.

**Note:** `pytest` and most CI jobs **do not** require Modal — HTTP clients are mocked. Use `serve` when exercising real embed/LLM/GPU paths.


## Staging model weights (D6 / D7)

Before marking FastEmbed or Qwen assets **verified** in `docs/sessions/S000-internal-docs-archive/data-staging-state.md`, populate Modal volumes:

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

## vecinita-embedding

- **Model:** `intfloat/multilingual-e5-small` (384-dim, ADR-048; supersedes English-only BGE / ADR-008)
- **Volume:** `embedding-models` (HF cache)
- **Endpoints:** `GET /health`, `POST /embed`, `POST /embed/batch`
- **Consumer env:** `VECINITA_MODAL_EMBED_URL` on DO backends (`packages/embedding-client`)

First deploy downloads weights into the Modal volume; allow several minutes on cold start.

**Staging:** `./scripts/stage_modal_weights.sh` (see `docs/sessions/S000-internal-docs-archive/data-staging-state.md`).

## vecinita-llm (prod vLLM — ADR-037)

- **Default model:** `Qwen/Qwen2.5-1.5B-Instruct` (ADR-009); playground tags via `llm_model_registry.py` on the **playground** app
- **GPU:** NVIDIA T4, `timeout=900s`, `scaledown_window=300` (scale-to-zero)
- **Volume:** `llm-models` (`/models`, `manifest.json`, `/models/repos/<tag>`); adapters volume for promoted LoRA (ADR-053)
- **Endpoints:** inference + `/warm` (proxy auth on mutating routes)
- **Consumer env:** `VECINITA_MODAL_LLM_URL` on DO chat-rag-backend (`packages/llm-client`)
- **GPU memory snapshots (ADR-022 / EV-313 / #313):** Kill-switch `VECINITA_LLM_GPU_SNAPSHOT`
  (default **off** until staging evidence). When on: prod-only `enable_memory_snapshot` +
  vLLM Level-1 sleep before capture / wake on restore; snapshot **base engine only**, resolve
  LoRA after restore (#316). Snapshot **creation** can take ~70s — prime via `/warm` after
  deploy (see #315). Do not enable on playground.
- **Eager A/B:** `VECINITA_LLM_ENFORCE_EAGER` (default `true`) — independent of snapshot switch
- **Deprecated:** `vecinita-ollama`, `VECINITA_MODAL_OLLAMA_URL` — do not deploy

## vecinita-llm-playground

- **Role:** Admin list/pull + sandbox eval `model_id` reloads (ADR-037)
- **Consumer env:** `VECINITA_MODAL_LLM_PLAYGROUND_URL` — never use for ChatRAG
- **Path aliases:** `GET/POST /models/ollama*` for FE compat
- **Snapshots:** remain **off** (`enable_memory_snapshot=False`) while model reload is allowed

**Modal secret `vecinita-llm`** (ASGI proxy auth only):

```bash
set -a && source prod.env && set +a
modal profile activate vecinita
bash scripts/deploy/sync_llm_secret.sh --apply
```

Key: `VECINITA_MODAL_PROXY_KEY` — must match DO `VECINITA_MODAL_PROXY_KEY` on internal-write-api.
After migration from `vecinita-ollama` secret, retire the old secret in the Modal dashboard.

**Operator de-deploy (post-smoke):**

```bash
modal app stop vecinita-ollama
```
