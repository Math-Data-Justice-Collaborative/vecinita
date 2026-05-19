# Feature List

> **Project**: Vecinita  
> **Repository**: `/root/GitHub/VECINA/vecinita`  
> **Last updated**: 2026-05-19  
> **Source**: 01-requirements interview (context-brief.md, [ADR index](adr/README.md))

## Summary

| # | Feature | Status | Category | App | Source |
|---|---------|--------|----------|-----|--------|
| F1 | Bilingual community Q&A (RAG chat) | Planned | ChatRAG | chat-rag-backend, chat-rag-frontend | User interview 01-requirements |
| F2 | Streaming query responses | Planned | ChatRAG | chat-rag-backend | User interview 01-requirements |
| F3 | Stateless chat (no server-side history) | Planned | ChatRAG | chat-rag-backend | ADR-004, user interview |
| F4 | LlamaIndex RAG orchestration | Planned | ChatRAG | chat-rag-backend, `packages/rag` | User interview 01-requirements |
| F5 | pgvector retrieval | Planned | ChatRAG | chat-rag-backend, database | context-brief R4 |
| F6 | Self-hosted LLM inference | Planned | ChatRAG | Modal (`vecinita-llm`) + chat-rag-backend | RD-021 vLLM primary; Ollama fallback per ADR-009 |
| F7 | URL scrape → chunk → embed → store | Planned | Data Management | data-management-backend | User interview 01-requirements |
| F8 | Ingest job queue & status API | Planned | Data Management | data-management-backend | User interview 01-requirements |
| F9 | Corpus list / delete (admin) | Planned | Data Management | data-management-backend, data-management-frontend | User interview 01-requirements |
| F10 | FastEmbed embeddings (384-dim) on Modal | Planned | Data Management | data-management-backend (Modal) | User interview 01-requirements |
| F11 | ChatRAG web UI (React/Vite) | Planned | ChatRAG | chat-rag-frontend | User interview 01-requirements |
| F12 | Data management admin UI | Planned | Data Management | data-management-frontend | User interview 01-requirements |
| F13 | Database migrations & pgvector | Planned | Database | apps/database | User interview 01-requirements |
| F14 | Seed corpus & eval fixtures | Planned | Database | apps/database | S1.13 audit; data-management-plan D1–D3 |
| F15 | Privacy schema guardrails & tests | Planned | Cross-cutting | database, all backends | ADR-004 |
| F16 | Infrastructure-only protection (data-mgmt APIs) | Planned | Cross-cutting | data-management-backend | ADR-004, ADR-002 |
| F17 | Basic observability (no PII in logs) | Planned | Cross-cutting | all deployables | User interview 01-requirements |
| F18 | Local dev: docker-compose + Modal serve | Planned | Cross-cutting | infra/ | User interview 01-requirements |

**Status key**: Implemented = production-ready, Planned = not yet built, Experimental = works but not validated

## Feature Details

### F1: Bilingual community Q&A (RAG chat)

- **What it does**: Answers community questions in English or Spanish using retrieved corpus context and a self-hosted LLM.
- **Inputs**: User question (text); optional language hint from client; corpus in Postgres/pgvector.
- **Outputs**: Answer text (and streamed tokens when streaming enabled).
- **Key parameters**:
  | Parameter | Default | Range | Description |
  |-----------|---------|-------|-------------|
  | `top_k` | `5` (`VECINITA_TOP_K`) | 1–50 | Retrieved chunks per query |
  | `chunk_size` | `256` tokens (`VECINITA_CHUNK_SIZE_TOKENS`) | ≥ 64 | Chunk size at ingest (see data-management) |
- **Limitations**: No server-side conversation memory across requests (F3). Auto-detect query language and respond in the same language.
- **Source**: User interview 01-requirements; context-brief §6 (bilingual worktree reference)

### F2: Streaming query responses

- **What it does**: Streams LLM tokens to the ChatRAG client for lower perceived latency.
- **Inputs**: Same as F1; client accepts SSE or equivalent stream.
- **Outputs**: Token stream + final metadata (sources, latency) without persisting message content server-side.
- **Limitations**: Must not write streamed content to durable logs or DB (ADR-004).
- **Source**: User interview 01-requirements

### F3: Stateless chat (no server-side history)

- **What it does**: Each request is independent; no `sessions` / `messages` tables or LangGraph checkpoints keyed to identity.
- **Inputs**: Single-turn or client-held multi-turn context in request body only (if multi-turn UX needed, context stays client-side).
- **Outputs**: Per-request response only.
- **Limitations**: No “resume conversation” across devices unless implemented in browser memory only.
- **Source**: ADR-004; user selected full ChatRAG core including stateless

### F4: LlamaIndex RAG orchestration

- **What it does**: Retrieval-augmented generation pipeline (retriever, synthesizer, optional tools) implemented with LlamaIndex in `packages/rag`, invoked from ChatRAG Backend.
- **Inputs**: Query string, DB connection, LLM/embedding client configuration.
- **Outputs**: Structured RAG result (answer, source nodes/chunk IDs).
- **Limitations**: Framework choice excludes LangGraph for v1; evaluate LlamaIndex version pins in dependency inventory.
- **Source**: User interview 01-requirements

### F5: pgvector retrieval

- **What it does**: Similarity search over chunk embeddings stored in DigitalOcean Managed Postgres (pgvector).
- **Inputs**: Query embedding (384-dim from F10).
- **Outputs**: Ranked chunks with scores and document metadata.
- **Limitations**: Single vector store (no Chroma in v1); dimension fixed at 384 for FastEmbed default.
- **Source**: context-brief R4; user interview

### F6: Self-hosted LLM inference

- **What it does**: Generates answers via self-hosted model on Modal (default architecture); ChatRAG Backend calls Modal HTTP with platform-injected credentials.
- **Inputs**: Prompt/messages, model name, generation params.
- **Outputs**: Completion text or stream.
- **Key parameters**:
  | Parameter | Default | Range | Description |
  |-----------|---------|-------|-------------|
  | `llm_backend` | `vllm` | `vllm` / `ollama` | vLLM primary (RD-021); Ollama fallback if cost proof fails in 04-tech-plan |
- **Limitations**: No paid third-party LLM APIs as default; external APIs require ADR exception. GPU sizing and model pin in 04-tech-plan.
- **Source**: RD-021, ADR-009; ADR-004

### F7: URL scrape → chunk → embed → store

- **What it does**: End-to-end ingest: fetch public URLs, normalize text, chunk, embed with FastEmbed, upsert into Postgres.
- **Inputs**: URL list or crawl config; job submission via Data Management API.
- **Outputs**: Documents, chunks, vectors in DB; job status records (URLs, status — no PII).
- **Limitations**: v1 HTML/text scrape only; multimodal/PDF deferred.
- **Source**: User interview 01-requirements

### F8: Ingest job queue & status API

- **What it does**: Async jobs on Modal with pollable status (`/jobs/*` pattern from sibling scraper reference).
- **Inputs**: Job create payload (URLs, options).
- **Outputs**: Job ID, status transitions, error codes.
- **Limitations**: Protected by infrastructure credentials only (F16).
- **Source**: User interview; context-brief §4.3

### F9: Corpus list / delete (admin)

- **What it does**: Operators list documents/chunks and delete corpus entries via Data Management Frontend + API.
- **Inputs**: API key / private network; document IDs.
- **Outputs**: Updated corpus state in Postgres.
- **Limitations**: No operator identity stored in Vecinita DB.
- **Source**: User interview 01-requirements

### F10: FastEmbed embeddings (384-dim) on Modal

- **What it does**: Batch/single embed endpoints on Modal using FastEmbed with model weights on Modal volume.
- **Inputs**: Text or batch of texts.
- **Outputs**: 384-dimensional vectors.
- **Limitations**: Modal pay-per-invoke; align migrations with `vector(384)`.
- **Source**: User interview; context-brief R8 (384-dim reference)

### F11: ChatRAG web UI (React/Vite)

- **What it does**: Public-facing chat interface for bilingual Q&A with streaming display.
- **Inputs**: User messages (browser only); calls ChatRAG Backend API.
- **Outputs**: Rendered answers; client-side UI state only.
- **Limitations**: No login; no analytics with identity.
- **Source**: User interview 01-requirements

### F12: Data management admin UI

- **What it does**: Admin SPA for job submission, corpus management, and job status (no personal login UI).
- **Inputs**: Deploy-time API key or platform SSO that does not persist identity in Vecinita DB.
- **Outputs**: Operator actions against Data Management API.
- **Source**: User interview 01-requirements

### F13: Database migrations & pgvector

- **What it does**: Alembic migrations enabling pgvector, documents/chunks/embeddings/jobs tables, forbidden-table checks.
- **Inputs**: Migration revisions in `apps/database`.
- **Outputs**: Versioned schema applied to DO Managed Postgres.
- **Source**: User interview 01-requirements

### F14: Seed corpus & eval fixtures

- **What it does**: Reproducible seed data and eval Q&A pairs for local/staging (no production PII).
- **Inputs**: Fixture files under `data/` (per data-management-plan).
- **Outputs**: Seeded DB for dev and CI.
- **Source**: Approved in 02-verify-plan (S1.13); [data-management-plan.md](data-management-plan.md) D1–D3

### F15: Privacy schema guardrails & tests

- **What it does**: Enforces zero personal data via schema deny-list, API rejection of identity fields, `tests/privacy/`, CI hooks.
- **Inputs**: Migrations, OpenAPI contracts.
- **Outputs**: Failing CI if forbidden tables/columns appear.
- **Source**: ADR-004 §Privacy enforcement

### F16: Infrastructure-only protection (data-mgmt APIs)

- **What it does**: Data Management routes require deploy secret, private network, or platform SSO without Vecinita `users` table.
- **Inputs**: `Authorization` or mTLS per deployment-integration plan.
- **Outputs**: Authorized admin operations without stored operator PII.
- **Source**: ADR-004, ADR-002

### F17: Basic observability (no PII in logs)

- **What it does**: Health endpoints, structured logs (request ID, latency, status), optional platform metrics; no raw prompts in persistent logs.
- **Inputs**: Application instrumentation.
- **Outputs**: Ops visibility within ADR-004 log rules.
- **Source**: User interview 01-requirements

### F18: Local dev: docker-compose + Modal serve

- **What it does**: Local Postgres+pgvector via docker-compose; APIs on host or compose; Modal `serve` for workers/embed/LLM during development.
- **Inputs**: `docker-compose.yml`, Modal CLI credentials.
- **Outputs**: Full stack dev without DO deploy.
- **Source**: User interview 01-requirements

## Feature Matrix

| Feature | ChatRAG | Data Mgmt | Database | Modal workers |
|---------|---------|-----------|----------|---------------|
| F1 Bilingual Q&A | Yes | No | No | No |
| F2 Streaming | Yes | No | No | No |
| F3 Stateless chat | Yes | No | No | No |
| F4 LlamaIndex RAG | Yes | No | No | No |
| F5 pgvector retrieval | Yes | No | Yes | No |
| F6 Self-hosted LLM | Yes | No | No | Yes |
| F7 Scrape pipeline | No | Yes | No | Yes |
| F8 Job queue API | No | Yes | No | Yes |
| F9 Corpus admin | No | Yes | Yes | No |
| F10 FastEmbed | No | Yes | No | Yes |
| F11 Chat UI | Yes | No | No | No |
| F12 Admin UI | No | Yes | No | No |
| F13 Migrations | No | No | Yes | No |
| F14 Seeds/fixtures | No | Partial | Yes | No |
| F15 Privacy enforcement | Yes | Yes | Yes | Yes |
| F16 Infra auth | No | Yes | No | No |
| F17 Observability | Yes | Yes | Yes | Yes |
| F18 Local dev | Yes | Yes | Yes | Yes |

## Out of Scope (v1)

| Item | Rationale | Source |
|------|-----------|--------|
| User/admin accounts, Supabase Auth, OAuth, invite-by-email | Zero personal data (ADR-004) | User interview |
| Paid third-party LLM/embed APIs as default | Cost + sovereignty (ADR-004) | User interview |
| RFantibody / PyRosetta / protein design | Wrong product domain; stale rules only | User interview |
| Multi-region / non-US deployment | Data sovereignty R10a | User interview |
| Analytics with identity (Segment, PostHog user IDs) | Zero personal data | User interview |
| Server-side chat history in DB | **Forbidden** — audited S1.14; F3 + ADR-004 | ADR-004 |

## Planned / Deferred (post-v1)

| # | Feature | Priority | Complexity | Notes |
|---|---------|----------|------------|-------|
| P1 | Dedicated API gateway / BFF | Medium | Medium | R6 unresolved — direct backend URLs in v1 |
| P2 | Multimodal / PDF ingest | Low | High | HTML scrape only in v1 |
| P3 | Model fine-tuning on corpus | Low | High | Fine-tuning excluded from v1 |
| P4 | Advanced admin (bulk reindex, A/B prompts) | Low | Medium | — |
| P5 | Full APM / OpenTelemetry | Low | Medium | Basic logs in v1 (F17) |

## Monorepo layout (confirmed)

```text
vecinita/
  apps/
    chat-rag-backend/
    chat-rag-frontend/
    data-management-backend/
    data-management-frontend/
    database/
  packages/
    rag/
    ingest/
    shared-schemas/
    embedding-client/
  infra/
    docker-compose.yml
    modal/
```
