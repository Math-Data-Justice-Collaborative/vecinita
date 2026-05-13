# 07 — Decomposition Candidates

> Auto-generated: 2026-05-12

## Extraction Priority Ranking

| Rank | Candidate | Score | Rationale |
|------|-----------|-------|-----------|
| 1 | **Agent extraction from gateway** | 9/10 | Coupling score 4 (Fused). Core AI logic mixed with HTTP routing. Clear domain boundary. User-stated priority. |
| 2 | **Embedding service to Modal worker** | 8/10 | Currently embedded in gateway. Natural fit for GPU worker. Different runtime (Modal vs Render). |
| 3 | **Scraper → Modal-only worker** | 7/10 | Currently dual-deployed (Render + Modal). Simplify to Modal-only background job. |
| 4 | **vLLM inference (new)** | 7/10 | Replaces model-modal with vLLM. New service, no extraction needed — pure creation. |
| 5 | **Data-management-api extraction** | 6/10 | Already somewhat separate (submodule). Needs cleaner API boundary. |
| 6 | **PgAdmin deployment** | 5/10 | Simple — add Docker image config + Render private service. |
| 7 | **Reindex worker (new)** | 4/10 | New service. No extraction needed. Can be created last. |

## Technical Decisions Resolved During Decomposition

See [specs/.technical-decisions-log.json](../specs/.technical-decisions-log.json) for full details.

| ID | Decision | Chosen |
|----|----------|--------|
| TD-001 | Directory layout | `apps/` + `packages/` |
| TD-002 | Database strategy | Schema-per-service |
| TD-003 | Local dev | Docker Compose with profiles |
| TD-004 | PgAdmin deploy | Render private service |
| TD-005 | CI strategy | Per-app workflows (path-filtered) |
| TD-006 | OpenAPI clients | Drop |

## Extraction Details

### 1. Agent Extraction

**What moves out of gateway**:
- `apis/gateway/src/agent/` — Full agent module (main.py, routers/, tools/, utils/)
- `apis/gateway/src/services/agent/` — Agent-domain services
- `apis/gateway/src/services/llm/` — LLM provider routing (becomes LlamaIndex)
- `apis/gateway/src/services/embedding/` — Embedding logic (moves to embedding-worker)
- `apis/gateway/src/services/corpus/` — Corpus retrieval (part of RAG pipeline)
- Relevant guardrails config

**What stays in gateway**:
- `apis/gateway/src/api/` — HTTP routing, middleware, auth
- `apis/gateway/src/services/db/` — Database service layer
- `apis/gateway/src/services/modal/` — Modal SDK integration
- `apis/gateway/src/services/scraper/` — Scraper orchestration
- `apis/gateway/src/services/ingestion/` — Ingestion pipeline orchestration

**New contract**: Gateway calls agent via HTTP REST (`POST /agent/query`, `POST /agent/stream`)

### 2. Embedding → Modal Worker

**What moves**:
- `apis/gateway/src/embedding/` — Embedding entry point
- `apis/gateway/src/embedding_service/` — Embedding service logic
- `modal-apps/embedding-modal/` — Current Modal embedding code

**Becomes**: `apps/embedding-worker/` — LlamaIndex-based embedding on Modal GPU

### 3. Scraper → Modal-Only

**What changes**:
- Remove Render deployment (vecinita-data-management-api-v1 on Render was serving scraper)
- Keep Modal deployment only
- `modal-apps/scraper/` → `apps/scraper-worker/`

### 4. vLLM Inference (New)

**Created from**:
- Rewrite of `modal-apps/model-modal/`
- Uses vLLM instead of custom inference code
- Exposes OpenAI-compatible API on Modal

### 5. Data Management API

**What moves**:
- `apis/data-management-api/` → `apps/data-management-api/`
- Deinit submodule, keep as local code
- Clean up to use `packages/db` for models

### 6. Reindex Worker (New)

**Created fresh**: New Modal worker for vector index rebuilds
