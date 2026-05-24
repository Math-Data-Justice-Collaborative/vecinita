# Feature List

> **Project**: Vecinita  
> **Repository**: `/root/GitHub/VECINA/vecinita`  
> **Last updated**: 2026-05-24  
> **Source**: 01-requirements interview (context-brief.md, [ADR index](adr/README.md)); **EV-001** delta (ADR-014)

## Summary

| # | Feature | Status | Category | App | Source |
|---|---------|--------|----------|-----|--------|
| F1 | Bilingual community Q&A (RAG chat) | Implemented | ChatRAG | chat-rag-backend, chat-rag-frontend | 11-verify-impl 2026-05-19 |
| F2 | Streaming query responses | Implemented | ChatRAG | chat-rag-backend | 11-verify-impl 2026-05-19 |
| F3 | Stateless chat (no server-side history) | Implemented | ChatRAG | chat-rag-backend | 11-verify-impl 2026-05-19 |
| F4 | LlamaIndex RAG orchestration | Implemented | ChatRAG | chat-rag-backend, `packages/rag` | 11-verify-impl 2026-05-19 |
| F5 | pgvector retrieval | Implemented | ChatRAG | chat-rag-backend, database | 11-verify-impl 2026-05-19 |
| F6 | Self-hosted LLM inference | Implemented | ChatRAG | Modal (`vecinita-llm`) + chat-rag-backend | T0 mocked; T3 live pending |
| F7 | URL scrape → chunk → embed → store | Implemented | Data Management | data-management-backend | 11-verify-impl 2026-05-19 |
| F8 | Ingest job queue & status API | Implemented | Data Management | data-management-backend | 11-verify-impl 2026-05-19 |
| F9 | Corpus list / delete (admin) | Implemented | Data Management | data-management-backend, data-management-frontend | 11-verify-impl 2026-05-19 |
| F10 | FastEmbed embeddings (384-dim) on Modal | Implemented | Data Management | data-management-backend (Modal) | D6 verified; live optional |
| F11 | ChatRAG web UI (React/Vite) | Implemented | ChatRAG | chat-rag-frontend | Vitest smoke; UI E2E waived v1 |
| F12 | Data management admin UI | Implemented | Data Management | data-management-frontend | Vitest smoke; UI E2E waived v1 |
| F13 | Database migrations & pgvector | Implemented | Database | apps/database | 11-verify-impl 2026-05-19 |
| F14 | Seed corpus & eval fixtures | Implemented | Database | apps/database | 11-verify-impl 2026-05-19 |
| F15 | Privacy schema guardrails & tests | Implemented | Cross-cutting | database, all backends | 11-verify-impl 2026-05-19 |
| F16 | Infrastructure-only protection (data-mgmt APIs) | Implemented | Cross-cutting | data-management-backend | 11-verify-impl 2026-05-19 |
| F17 | Basic observability (no PII in logs) | Implemented | Cross-cutting | all deployables | 11-verify-impl 2026-05-19 |
| F18 | Local dev: docker-compose + Modal serve | Implemented | Cross-cutting | infra/ | 11-verify-impl 2026-05-19 |
| F19 | Public corpus browse & tag filter | Planned | ChatRAG | chat-rag-backend, chat-rag-frontend | EV-001 01-requirements 2026-05-24 |
| F20 | LLM auto-tagging at ingest + admin re-tag | Planned | Data Management | data-management-backend, Modal LLM | EV-001 01-requirements 2026-05-24 |
| F21 | Admin chunk viewer & tag editor | Planned | Data Management | data-management-frontend, internal-write-api | EV-001 01-requirements 2026-05-24 |
| F22 | Tag-aware RAG retrieval | Planned | ChatRAG | chat-rag-backend, packages/rag | EV-001 01-requirements 2026-05-24 |

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
| F19 Corpus browse | Yes | No | No | No |
| F20 LLM tagging | No | Yes | Yes | Yes |
| F21 Admin chunks/tags | No | Yes | Yes | No |
| F22 Tag-filtered RAG | Yes | No | Yes | No |

## Out of Scope (v1)

| Item | Rationale | Source |
|------|-----------|--------|
| User/admin accounts, Supabase Auth, OAuth, invite-by-email | Zero personal data (ADR-004) | User interview |
| Paid third-party LLM/embed APIs as default | Cost + sovereignty (ADR-004) | User interview |
| RFantibody / PyRosetta / protein design | Wrong product domain; stale rules only | User interview |
| Multi-region / non-US deployment | Data sovereignty R10a | User interview |
| Analytics with identity (Segment, PostHog user IDs) | Zero personal data | User interview |
| Server-side chat history in DB | **Forbidden** — audited S1.14; F3 + ADR-004 | ADR-004 |

### F19: Public corpus browse & tag filter

- **What it does**: Community members browse the public corpus, filter by tags, search by title/URL text, and open the original source URL (external link).
- **Inputs**: Optional tag filters; optional search query (`q`); pagination (`page`, `page_size` default 20).
- **Outputs**: Paginated document list (id, title, url, language, tags); document detail with tags and source URL.
- **Key parameters**:
  | Parameter | Default | Range | Description |
  |-----------|---------|-------|-------------|
  | `page_size` | `20` (`VECINITA_BROWSE_PAGE_SIZE`) | 1–100 | Documents per browse page |
- **Limitations**: No in-app full-text reader — open document navigates to **original URL** (RD-026). No login. Public read API on ChatRAG backend only.
- **Source**: EV-001 / ADR-014; user interview 2026-05-24

### F20: LLM auto-tagging at ingest + admin re-tag

- **What it does**: After chunking, LLM assigns document-level tags (and optional chunk tags) from hybrid vocabulary; admin can re-run LLM tagging or edit tags manually.
- **Inputs**: Document text/chunks; seeded suggested tag list; admin trigger per document (single-document retag in v1).
- **Outputs**: Tag rows with `source: llm | human`; max **10** tags per document, **5** per chunk (RD-028).
- **Key parameters**:
  | Parameter | Default | Description |
  |-----------|---------|-------------|
  | `max_tags_per_document` | `10` | Hard cap |
  | `max_tags_per_chunk` | `5` | Hard cap |
- **Limitations**: Tag labels match `document.language` (en/es) (RD-030). Self-hosted Modal LLM only (ADR-009). No operator identity stored (ADR-004).
- **Source**: EV-001 / ADR-014

### F21: Admin chunk viewer & tag editor

- **What it does**: Operators view chunk list for a document (read-only text) and edit tags at document and chunk level (human or trigger LLM re-tag).
- **Inputs**: Infrastructure auth; document_id; tag payloads.
- **Outputs**: Updated `document_tags` / `chunk_tags` via internal-write API.
- **Limitations**: No Vecinita user accounts (F16). Chunk tags **union** with document tags at retrieval (RD-025).
- **Source**: EV-001 / ADR-014

### F22: Tag-aware RAG retrieval

- **What it does**: Retrieval filters chunks by tags when user selects tag chips in chat sidebar; if no tags selected, LLM infers relevant tags from the question.
- **Inputs**: `AskRequest` with optional `tags[]`; question text for LLM tag inference.
- **Outputs**: Filtered retrieval + answer; when user selected tags, **only user tags apply** (LLM inference skipped) (RD-027).
- **Limitations**: Tag filter is pre-retrieval SQL join; must not log tag selections as identity (ADR-004).
- **Source**: EV-001 / ADR-014

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
