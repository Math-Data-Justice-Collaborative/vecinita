# Feature List

> **Project**: Vecinita  
> **Repository**: `/root/GitHub/VECINA/vecinita`  
> **Last updated**: 2026-06-13  
> **Source**: 01-requirements interview (context-brief.md, [ADR index](adr/README.md)); **EV-001** delta (ADR-014); **EV-002** delta (ADR-016); **EV-003** F30 (ADR-018); **EV-004** delta F31 (ADR-019, ADR-020); **S003** delta F33 (ADR-023)
> **Last updated**: 2026-06-26 (S003 F33 — browser-local persistent chat history)

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
| F19 | Public corpus browse & tag filter | Implemented | ChatRAG | chat-rag-backend, chat-rag-frontend | 11-verify-impl 2026-05-25 |
| F20 | LLM auto-tagging at ingest + admin re-tag | Implemented | Data Management | data-management-backend, Modal LLM | 11-verify-impl 2026-05-25 |
| F21 | Admin chunk viewer & tag editor | Implemented | Data Management | data-management-frontend, internal-write-api | 11-verify-impl 2026-05-25 |
| F22 | Tag-aware RAG retrieval | Implemented | ChatRAG | chat-rag-backend, packages/rag | 11-verify-impl 2026-05-25 |
| F23 | Admin UI CSS/UX overhaul (shadcn/ui) | Implemented | Data Management | data-management-frontend | 11-verify-impl 2026-05-27 |
| F24 | Tag display in corpus list | Implemented | Data Management | data-management-frontend, internal-write-api | 11-verify-impl 2026-05-27 |
| F25 | Admin summary dashboard | Implemented | Data Management | data-management-frontend, internal-write-api | 11-verify-impl 2026-05-27 |
| F26 | System health check dashboard | Implemented | Cross-cutting | data-management-frontend, all services | 11-verify-impl 2026-05-27 |
| F27 | Bulk corpus operations | Implemented | Data Management | data-management-frontend, internal-write-api | 11-verify-impl 2026-05-27 |
| F28 | Source serving statistics | Implemented | Cross-cutting | chat-rag-backend, internal-write-api, database | 11-verify-impl 2026-05-27 |
| F29 | Audit log & version history | Implemented | Data Management | internal-write-api, data-management-frontend, database | 11-verify-impl 2026-05-27 |
| F30 | Strict static typing (no `Any` / `any`) | Implemented | Cross-cutting | all Python + TS apps | EV-003 2026-05-27 |
| F31 | Admin + shared frontend bilingual UI (en/es) | Planned | Cross-cutting | data-management-frontend, chat-rag-frontend, `packages/frontend-i18n`, `packages/frontend-ui` | EV-004 2026-06-13 |
| F32 | Admin Job Management tab (list jobs) | Implemented | Data Management | data-management-backend, data-management-frontend | S002 2026-06-26 (#89) |
| F33 | Browser-local persistent chat history (localStorage + previous-chats list) | Planned | ChatRAG | chat-rag-frontend | S003 2026-06-26; ADR-025 2026-06-28 |

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
- **Client-side boundary (F33)**: F3 forbids **server-side** history only. F33 adds **device-local** chat persistence in the browser via `localStorage` (ADR-025; originally `sessionStorage` per ADR-023) — never transmitted to the server, never written to the database or logs. F3 (server stays stateless) and F15 privacy guardrails are unaffected.
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
| F23 Admin UI shadcn/ui | No | Yes | No | No |
| F24 Tag display in list | No | Yes | No | No |
| F25 Admin dashboard | No | Yes | Yes | No |
| F26 Health check dashboard | Yes | Yes | No | Yes |
| F27 Bulk corpus ops | No | Yes | Yes | No |
| F28 Serving statistics | Yes | Yes | Yes | No |
| F29 Audit log & versions | No | Yes | Yes | No |
| F30 Strict static typing | Yes | Yes | Yes | Yes |
| F31 Bilingual UI (shared packages) | Yes | Yes | No | No |
| F32 Admin Job Management tab | No | Yes | No | No |
| F33 Persistent chat history (browser-local) | Yes | No | No | No |

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

### F23: Admin UI CSS/UX overhaul (shadcn/ui)

- **What it does**: Modernizes the data-management-frontend with shadcn/ui components (Tailwind + Radix), system-preference light/dark theme, polished layout, and accessible component patterns.
- **Inputs**: Existing components (JobForm, CorpusList, DocumentAdmin) refactored to use shadcn primitives.
- **Outputs**: Visually cohesive admin interface with consistent spacing, typography, color tokens, and responsive layout.
- **Key dependencies**: tailwindcss, @radix-ui/*, class-variance-authority, clsx, tailwind-merge, lucide-react.
- **Limitations**: Admin UI only — chat-rag-frontend is a separate concern. No new functionality, purely presentational overhaul.
- **Source**: EV-002 / user interview 2026-05-26

### F24: Tag display in corpus document list

- **What it does**: Shows document tags as colored chips/badges inline under each document title in the corpus list view, without requiring the user to open the DocumentAdmin panel.
- **Inputs**: Document list API response extended to include tags per document.
- **Outputs**: Tag chips rendered below document title in CorpusList; color-coded by source (LLM vs human).
- **Limitations**: Read-only display; editing still requires opening DocumentAdmin or using bulk operations (F27).
- **Source**: EV-002 / user interview 2026-05-26

### F25: Admin summary dashboard

- **What it does**: Dedicated dashboard panel showing aggregated system statistics for the corpus and platform.
- **Inputs**: New backend stats endpoint(s) returning aggregated counts and distributions.
- **Outputs**: Dashboard cards/widgets displaying:
  | Statistic | Description |
  |-----------|-------------|
  | Total documents | Count of documents in corpus |
  | Total chunks | Count of chunks across all documents |
  | Tag distribution | Top tags by document count (bar/list) |
  | Job statistics | Total jobs, success/fail rate, recent jobs |
  | Language breakdown | Documents per language (en/es/other) |
  | Recent activity | Latest ingests, edits, deletions feed |
  | Storage usage | Estimated DB size |
  | Top served documents | Most-cited documents from F28 stats |
- **Limitations**: Stats are point-in-time snapshots (no real-time streaming). Storage size is an estimate from `pg_total_relation_size`.
- **Source**: EV-002 / user interview 2026-05-26

### F26: System health check dashboard

- **What it does**: Admin dashboard page showing live health status of all Vecinita services, with manual refresh.
- **Inputs**: Frontend calls each service's `/health` endpoint directly (requires CORS from all services).
- **Outputs**: Service status grid showing up/down/degraded for:
  | Service | Health endpoint |
  |---------|----------------|
  | Internal Write API (DO) | `GET /health` |
  | Data Management Backend (Modal) | `GET /health` |
  | Chat RAG Backend (DO) | `GET /health` |
  | Chat RAG Frontend (DO) | HTTP 200 check |
  | Data Management Frontend (DO) | HTTP 200 check |
  | PostgreSQL | Connection check via internal-write-api |
  | Modal vLLM | `/health` or model endpoint |
  | Modal FastEmbed | `/health` endpoint |
- **Key parameters**:
  | Parameter | Default | Description |
  |-----------|---------|-------------|
  | `VECINITA_HEALTH_TIMEOUT_MS` | `5000` | Timeout per service health check |
- **Limitations**: Manual refresh only (no auto-poll). Frontend-initiated checks require CORS headers on all services. Postgres health proxied through internal-write-api (not direct connection from browser).
- **Source**: EV-002 / user interview 2026-05-26

### F27: Bulk corpus operations

- **What it does**: Multi-select documents in the admin corpus list and apply bulk actions: delete, tag, LLM re-tag, edit metadata (title/language).
- **Inputs**: Checkbox + shift+click selection UI; bulk action toolbar; confirmation dialogs for destructive actions.
- **Outputs**: Bulk operations applied to selected documents via batch API calls; audit log entries for each affected document (F29).
- **Supported bulk actions**:
  | Action | API call | Destructive |
  |--------|----------|-------------|
  | Bulk delete | `DELETE /internal/v1/documents/bulk` | Yes (confirm) |
  | Bulk tag | `PATCH /internal/v1/documents/bulk/tags` | No |
  | Bulk LLM re-tag | `POST /internal/v1/documents/bulk/retag` | No |
  | Bulk edit metadata | `PATCH /internal/v1/documents/bulk/metadata` | No |
- **Limitations**: No bulk content editing (content changes require re-ingest). Bulk delete is irreversible (but audit log preserves record of deletion). Maximum 100 documents per bulk operation.
- **Source**: EV-002 / user interview 2026-05-26

### F28: Source serving statistics

- **What it does**: Tracks how many times each document was cited in a successful RAG response, displayed on the admin summary dashboard.
- **Inputs**: After each successful RAG answer, chat-rag-backend asynchronously POSTs document IDs to `POST /internal/v1/stats/served` on internal-write-api.
- **Outputs**: `document_serving_stats` table with per-document served count and last-served timestamp; displayed in F25 dashboard as "Top served documents".
- **Key parameters**:
  | Parameter | Default | Description |
  |-----------|---------|-------------|
  | `VECINITA_STATS_ENABLED` | `true` | Enable/disable serving stats recording |
- **Schema**: `document_serving_stats(document_id UUID FK, served_count INTEGER DEFAULT 0, last_served_at TIMESTAMPTZ)`
- **Limitations**: Document-level only (not chunk-level). Counter increments on successful response only. Async fire-and-forget POST — stats failure does not affect RAG response. Dashboard display only (not shown inline in corpus list).
- **Source**: EV-002 / user interview 2026-05-26

### F29: Audit log & version history

- **What it does**: Immutable event log tracking all corpus modifications plus metadata/tag version snapshots, viewable as a global log and per-document history timeline.
- **Inputs**: All write operations on documents, chunks, tags, and jobs automatically emit audit events. No personal data stored — uses `request_id` for correlation only (ADR-016).
- **Outputs**: Two new tables and two UI views:
  | Table | Purpose |
  |-------|---------|
  | `audit_log` | Immutable event stream (event_type, entity_type, entity_id, request_id, payload JSONB, created_at) |
  | `document_versions` | Metadata/tag snapshots (document_id, version_number, title, language, tags_snapshot JSONB, created_at) |
- **Event types**:
  | Event | Trigger |
  |-------|---------|
  | `document.created` | Ingest completes |
  | `document.deleted` | Single or bulk delete |
  | `document.edited` | Metadata change (title, language) |
  | `document.tagged` | Tags added/removed (human or LLM) |
  | `document.retagged` | LLM re-tag triggered |
  | `bulk_action` | Any bulk operation (payload lists affected IDs) |
  | `job.state_change` | Job status transition |
- **UI views**:
  | View | Location |
  |------|----------|
  | Global audit log | New admin page — filterable by event type, entity, date range |
  | Per-document history | Document detail panel — chronological timeline of changes |
- **Key parameters**:
  | Parameter | Default | Range | Description |
  |-----------|---------|-------|-------------|
  | `VECINITA_AUDIT_RETENTION_DAYS` | `365` | 30–∞ | Days to retain audit records (0 = forever) |
- **Limitations**: No IP addresses stored (ADR-016). No personal data. Version history covers metadata + tags only (not chunk text content). Configurable retention with background cleanup job.
- **Source**: EV-002 / user interview 2026-05-26; ADR-016

### F30: Strict static typing (no `Any` / `any`)

- **What it does**: Blocks `typing.Any` in Python and `any` in TypeScript across CI, hooks, and documented local commands.
- **Inputs**: Source changes in `apps/`, `packages/`, `tests/`, and both frontends.
- **Outputs**: Failing CI/lint on explicit or unsafe-any violations; `docs/typing-policy.md` as developer reference.
- **Key tools**:
  | Layer | Tool | Rule |
  |-------|------|------|
  | Python lint | Ruff | `ANN401` |
  | Python types | basedpyright | `reportExplicitAny` |
  | TS lint | typescript-eslint | `no-explicit-any`, `no-unsafe-*` |
  | TS compile | `tsc` | `strict`, `noImplicitAny` |
- **Limitations**: `reportAny` and ESLint `strictTypeChecked` not enabled (see typing-policy).
- **Source**: EV-003; ADR-018

### F31: Admin + shared frontend bilingual UI (en/es)

- **What it does**: Delivers full static UI translation (English/Spanish) for the admin dashboard, mirrors ChatRAG locale behavior, and extracts shared i18n + UI packages consumed by both browser SPAs.
- **Inputs**: Operator browser; optional prior `vecinita.locale` in `localStorage`; browser language for first visit.
- **Outputs**: Rendered admin UI in selected locale; `document.documentElement.lang` set; dates formatted with UI locale; shared EN/ES message tables via `t(locale, key)`.
- **Key parameters**:
  | Parameter | Default | Range | Description |
  |-----------|---------|-------|-------------|
  | `vecinita.locale` | Browser-detected | `en` \| `es` | Shared `localStorage` key across both frontends |
  | Browser fallback | `es` | — | Non-en/es browser languages default to Spanish (match ChatRAG) |
- **Shared packages**:
  | Package | npm name | Exports |
  |---------|----------|---------|
  | `packages/frontend-i18n` | `vecinita-frontend-i18n` | `Locale`, `detectBrowserLocale()`, `readStoredLocale()`, dot-prefixed `t()` (`chat.*`, `admin.*`, `shared.*`) |
  | `packages/frontend-ui` | `vecinita-frontend-ui` | `LocaleProvider`, `useLocale`, `LanguageToggle`, `ThemeToggle`, `TagFilterChips`, `TagBadge`, `PaginationControls`; minimal shadcn re-exports (Button, Badge, Input, Label, Dialog) |
- **Admin scope**: ~120+ static strings across Dashboard, Corpus, Health, Audit, bulk dialogs; EN/ES toggle in sidebar footer beside `ThemeToggle` (desktop + mobile sheet).
- **ChatRAG scope**: Migrate app-local i18n to shared packages; **full Tailwind migration** of ChatRAG layout (not minimal scan-only); consume shared components.
- **Limitations**: UI chrome only — corpus document titles, tag labels, URLs, audit JSON payloads, API `error_message`, and health/job status enums remain in source form (R30). No backend or API contract changes. No `Accept-Language` header in F31.
- **Priority**: High — ship in EV-004 before next deploy.
- **Source**: EV-004 user interview 2026-06-13; ADR-019, ADR-020 (amended); context-brief §13

### F32: Admin Job Management tab (list jobs)

- **What it does**: Adds a Job Management tab to the admin dashboard that lists all ingest/retag jobs (running, completed, failed) sourced from a new server-backed list endpoint. Because job state is read from the server (not component-local React state), switching tabs and returning no longer drops running/failed job info (the original symptom in #89; same class as #53).
- **Inputs**: Operator browser; `GET /jobs` on the data-management backend (optional `?status=` filter).
- **Outputs**: Table of jobs with short job id, type (ingest/retag), status badge, source URLs, last-updated time, and `error_code: error_message` for failed jobs; polled while open; manual refresh.
- **Backend**: `GET /jobs` list endpoint (newest first) + `list_jobs()` on `JobStore` / `DictJobStore` / `InMemoryJobStore`; `job_type` added to the `Job` schema; `JobList` response model; OpenAPI `openapi/data-management.yaml` updated.
- **Frontend**: New `/jobs` route + sidebar nav item (`ListChecks`); `JobsPage`; `listJobs()` client; en/es i18n (`admin.nav.jobs`, `admin.jobs.*`).
- **Limitations**: No PII in listings (URLs + status only, ADR-004). No job cancellation/retry in this iteration. Status/type enums localized; error messages remain in source form (consistent with F31 R30).
- **Priority**: High — pairs with #88 ingest tag resilience.
- **Source**: S002 session (GitHub #89); related bug #88 (graceful ingest tagging).

### F33: Browser-local persistent chat history (sessionStorage + previous-chats list)

- **What it does**: Persists the ChatRAG main-page conversation in the browser so it is **not lost on page refresh**, when leaving the tab and returning, when **closing and reopening the tab**, or in a **new tab** of the same origin, and keeps a selectable **list of previous conversations** the user can revisit. All storage is device-local via `localStorage` (ADR-025; originally `sessionStorage` per ADR-023) — never sent to the server, database, or logs.
- **Inputs**: Community member browser. Active conversation state (`useChatHistory`) lifted to the always-mounted `AppContent` shell (existing, from #53/PR #68); a "New chat" action; selecting/deleting a previous conversation.
- **Outputs**:
  - **Active conversation** rehydrated from `sessionStorage` on mount (survives refresh + tab-away/return within the same tab).
  - **Previous-chats list** rendered on the main page; selecting one loads it as the active conversation.
- **Key parameters / decisions**:
  | Parameter | Value | Source |
  |-----------|-------|--------|
  | Storage mechanism | **`localStorage`** (device-local; durable across tab close; shared across tabs of the same origin; never leaves the device) | ADR-025 (reverses R41/R43 `sessionStorage`) |
  | Conversation boundary | Explicit **"New chat"** button archives the current conversation and starts a fresh one | R44 |
  | History cap | Keep the **last 10** conversations, FIFO eviction of oldest | R45 |
  | Previous-chat label | **First user message** (truncated) **+ relative timestamp** (e.g. "2h ago") | R46 |
  | Clear semantics | **"Clear"** resets the active conversation; **per-item delete** + **"Clear all history"** manage the list; `sessionStorage` updated accordingly | R47 |
- **Limitations / scope**:
  - **Device-local & durable** (ADR-025) — history survives tab close / browser restart and is readable by new tabs of the same origin. **Live** sync between two simultaneously-open tabs (via `storage` events) is **not** implemented; concurrent tabs use last-write-wins. No cross-device or cross-browser sync.
  - No **server-side** chat/session persistence — F3 and ADR-004 server-statelessness are preserved (see ADR-023/025). No backend, API, or contract changes.
  - Must serialize message list + sources safely and degrade gracefully when `localStorage` is full or disabled (no crash; fall back to in-memory).
  - Frontend-only delta in `apps/chat-rag-frontend`; no change to `data-management-frontend`.
- **Priority**: High — direct user request (S003).
- **Source**: S003 session interview 2026-06-26 (R43–R47); context-brief §14 (F33, R39–R42); ADR-023; **ADR-025** (2026-06-28 — `localStorage` durable/cross-tab, reverses `sessionStorage`).

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
    frontend-i18n/       # EV-004 F31 — locale utils + EN/ES messages
    frontend-ui/         # EV-004 F31 — shared React + Tailwind components
  infra/
    docker-compose.yml
    modal/
```
