# Feature List

> **Project**: Vecinita  
> **Repository**: `/root/GitHub/VECINA/vecinita`  
> **Last updated**: 2026-06-13  
> **Source**: 01-requirements interview (context-brief.md, [ADR index](adr/README.md)); **EV-001** delta (ADR-014); **EV-002** delta (ADR-016); **EV-003** F30 (ADR-018); **EV-004** delta F31 (ADR-019, ADR-020); **S003** delta F33 (ADR-023); **EV-005** delta F34 (ADR-026)
> **Last updated**: 2026-07-10 (S010/EV-011 F39 follow-on — client consolidation RD-163–RD-172)

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
| F34 | Supabase Auth for admin surfaces (invite-only, admin+viewer) | Planned | Cross-cutting (admin) | data-management-frontend, data-management-backend, internal-write-api | S004/EV-005 2026-06-28; ADR-026 (#75) |
| F35 | Admin user management + remember-me + Resend SMTP/templates | Planned | Cross-cutting (admin) | data-management-frontend, data-management-backend, supabase config + CI | S005/EV-006 2026-06-29; ADR-029 (#75) |
| F36 | Admin RAG evaluation tab + golden eval set | Implemented | Data Management | data-management-frontend, internal-write-api, packages/eval | S007/EV-008 2026-07-01; #99 |
| F37 | Eval UX polish + playground + runtime config promote | Planned | Data Management + ChatRAG | data-management-frontend, internal-write-api, data-management-backend, chat-rag-backend | S008/EV-009 2026-07-02 |
| F38 | Playground model download (super-admin) | Implemented | Data Management | data-management-frontend, internal-write-api, Modal LLM app | S009/EV-010 2026-07-05; backend unified in F39 |
| F39 | Unified LLM Modal service (deprecate `vecinita-ollama`) | Planned | Cross-cutting | `infra/modal/llm_app.py`, `packages/llm-client`, all LLM consumers | S010/EV-011; ADR-037; follow-on RD-163–RD-172 |

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
| F34 Supabase admin auth | No | Yes | No | No |
| F35 Admin user management + auth UX | No | Yes | No | No |

## Out of Scope (v1)

| Item | Rationale | Source |
|------|-----------|--------|
| ~~User/admin accounts, Supabase Auth, OAuth, invite-by-email~~ → **partially admitted in EV-005 (F34)** for **admin surfaces only**: Supabase Auth + email invite + password login + `admin`/`viewer` roles. EV-006 (F35) further admits **in-app operator lifecycle management** (invite/list/role/resend/disable/revoke/admin-reset), **remember-me**, **self-service password reset**, and **repo-versioned Resend SMTP emails**. **OAuth/social login, MFA/2FA, and bulk CSV user import remain out of scope.** Visitor (ChatRAG) auth still excluded. | Admin-surface auth + operator management required by #75; ADR-026/ADR-029 supersede ADR-004 auth clause for admin only | User interview; #75; ADR-026; ADR-029 |
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

### F34: Supabase Auth for admin surfaces (invite-only, admin + viewer)

- **What it does**: Adds a real **authentication interface** ([#75](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/75)) over the **admin surfaces** using **Supabase Auth**, so only permitted operators can manage the corpus, view dashboards, and call admin APIs. Registration is **invitation-only**. The public ChatRAG experience stays **anonymous and stateless** (F3 preserved). Supersedes the ADR-004 *no Supabase Auth / no identity* clause **for admin surfaces only** (ADR-026).
- **Protected surfaces**:
  | Surface | Path | Auth change |
  |---------|------|-------------|
  | Data Management UI | `apps/data-management-frontend/` | Login screen, `@supabase/supabase-js` session, protected routes, current-user display, logout |
  | Data Management API | `apps/data-management-backend/` | Supabase JWT verification; `401` on missing/invalid token |
  | Internal Write API | `apps/internal-write-api/` | Supabase JWT verification + role check; `403` for `viewer` on writes |
- **Unchanged (anonymous)**: ChatRAG chat/query API + public corpus browse stay anonymous (no login). ChatRAG API additionally tightens **CORS to the ChatRAG frontend origin only** (RD-079).
- **Inputs**: Operator browser; admin email invitation; email + password login; Supabase JWT (`Authorization: Bearer`) on admin API requests.
- **Outputs**: Authenticated admin sessions; `401`/`403` for unauthenticated/under-privileged requests; audit log attributed to the **opaque Supabase user UUID + role** (no email/name in corpus DB).
- **Key decisions**:
  | Topic | Decision | Source |
  |-------|----------|--------|
  | Scope | Admin surfaces only; ChatRAG anonymous | R49, RD-073 |
  | Registration | Invitation-only (public sign-up disabled) | R51, RD-074 |
  | Credentials | Email + password; admin invites by email link | RD-074 |
  | Roles | `admin` (full) + `viewer` (read-only) | R51, RD-075 |
  | Token transport | SPA `supabase-js` session → `Authorization: Bearer` JWT; FastAPI verifies | RD-076 |
  | Identity / PII residency | Identity in Supabase; corpus DB PII-free; audit actor = opaque Supabase UUID + role | R50, RD-077 |
  | Environment syncing | Supabase **branching** on canonical project; migrations in repo; secrets via Modal/DO env | R52, RD-078 |
  | ChatRAG CORS | Strict — only the ChatRAG frontend origin | RD-079 |
- **Limitations / scope**: No OAuth/social login (this cycle). No RBAC beyond `admin` + `viewer`. No visitor authentication. No operator PII in the Vecinita corpus DB (only opaque UUID + role for attribution). Secrets never committed (no-operator-spec-commits). Cost of Supabase Auth + branching is sized against the ADR-004 ≤ $50/mo cap in 04-tech-plan.
- **Privacy (F15 extended, not relaxed)**: corpus DB keeps the forbidden-table deny-list (`users`, `accounts`, `sessions`, `messages`, `profiles`, `invites`, `auth_*`); Supabase manages its own `auth.*` schema in a separate database; `audit_log` may add only `actor_id` (UUID) + `actor_role`.
- **Priority**: High — direct user request (#75); unblocks per-user dashboards and audit attribution.
- **Source**: S004 / EV-005 interview 2026-06-28 (RD-073–RD-079); context-brief §15; ADR-026; #75.

### F35: Admin user management + remember-me + Resend SMTP/templates

- **What it does**: Builds operator-facing auth tooling on top of F34 so the team manages users
  **in-app** (no Supabase Dashboard dependency), stays signed in across browser restarts, recovers
  forgotten passwords, and ships **versioned bilingual auth emails** through **Resend**, synced to
  Supabase via CI/CD.
- **Protected surfaces**:
  | Surface | Path | Change |
  |---------|------|--------|
  | Data Management UI | `apps/data-management-frontend/` | New `/users` page + sidebar nav (admin-only); remember-me checkbox + "Forgot password?" link on login; in-app reset page |
  | Data Management API | `apps/data-management-backend/` (host TBD 04-tech-plan) | New admin-only `/admin/users*` endpoints wrapping the Supabase **Admin API** (service key server-side only) |
  | Supabase config | `supabase/config.toml`, `supabase/templates/` | `[auth.email.smtp]` (Resend), 6 versioned bilingual templates, rate-limit/expiry settings |
  | CI/CD | `.github/workflows/supabase.yml` | Validate template paths offline; `config push` templates on merge to `main`; pinned Supabase CLI |
- **Sub-features**:
  | # | Capability | Detail |
  |---|-----------|--------|
  | F35.1 | User management page | List operators (email, role, status, last sign-in); invite (email + role); change role; resend invite; disable/enable (ban/unban); revoke (delete); admin-triggered password reset. Admin-only; `viewer` → `403` and controls hidden. |
  | F35.2 | Remember-me | Login checkbox (**default checked**). Checked → session in `localStorage` (survives restart); unchecked → `sessionStorage` (clears on tab close). Preference persisted in `localStorage` key `vecinita.auth.remember`; storage adapter chosen before `createClient` (supabase-js has no native flag). |
  | F35.3 | Self-service password reset | "Forgot password?" link → Supabase recovery email → in-app reset page completes via `updateUser`. |
  | F35.4 | Resend SMTP (hybrid) | Resend provisions API key + verified domain; SMTP encoded in `config.toml` (`pass = env(SUPABASE_SMTP_PASS)`) so `config push` is the single source of truth. `smtp.resend.com:465`, user `resend`. |
  | F35.5 | Versioned bilingual templates | Six surfaces (invite, recovery, confirmation, magic_link, email_change, security notifications) as HTML in `supabase/templates/`, **stacked bilingual** (EN section + ES section). |
  | F35.6 | CI/CD sync | `supabase.yml` validate (offline path lint) + `sync-production` (`config push` with template HTML, CLI ≥ #5686, pinned). |
  | F35.7 | Idle/session timeout | Client-side inactivity timer (default **30 min**) with a **1-min warning modal**; signs out the current device (`signOut({scope:"local"})`) → login. Config `VITE_VECINITA_IDLE_TIMEOUT_MIN`/`_WARNING_SEC`. Frontend-only. (ADR-031 TP-S005-17) |
  | F35.8 | Log out of all devices | Self-service account action calling global `signOut()` (revokes all refresh tokens) **and** an admin **force-logout** of another operator via `POST /admin/users/{id}/signout`. (ADR-031 TP-S005-18/19) |
  | F35.9 | User search + pagination | Server-side email search (`q` ≥ 3 chars → GoTrue `filter`) + `page`/`page_size` with shared `PaginationControls`. (ADR-031 TP-S005-20) |
  | F35.10 | Audit viewer for user events | Reuse F29 AuditPage + `GET /internal/v1/audit`; add `entity_type` "Users" filter, i18n labels for `user.*`/`email.*` events, and a per-row "View activity" link. (ADR-031 TP-S005-21) |
  | F35.11 | Deliverability test-send | Admin "Send test email" → `POST /admin/email/test` via Resend REST (proves domain + SPF/DKIM/DMARC); + operator DNS checklist in the runbook. (ADR-031 TP-S005-22/23) |
  | F35.12 | Redirect URL wiring (EV-007) | Backend passes `redirect_to={VECINITA_ADMIN_FRONTEND_URL}/accept-invite` on invite/resend and `…/reset-password` on admin-triggered recovery; Supabase `site_url` + `additional_redirect_urls` synced via `config push` (staging-first). |
  | F35.13 | Auth callback pages (EV-007) | `/accept-invite` and `/reset-password` parse hash/query (`access_token`, `code`, `#error=…`); wait for session before password form; bilingual expired-link UX with admin-resend guidance. |
  | F35.14 | Retract invitation (EV-007) | `POST /admin/users/{id}/revoke-invite` for `status=invited` only; distinct UI label from "Delete user"; audit `user.invite_revoked`. |
  | F35.15 | Invite lifecycle UI + template polish (EV-007) | Users list shows `invited_at` + "~1h expiry" hint for pending invites; invite/recovery template copy/branding polish aligned with `otp_expiry`. |
- **Key parameters / decisions**:
  | Item | Value | Source |
  |------|-------|--------|
  | Remember-me default | **Checked** (persist) | RD-084 |
  | Remember-me key | `vecinita.auth.remember` (`localStorage`) | RD-084 |
  | SMTP sourcing | **Hybrid** — Resend creds, config.toml is source of truth | RD-085 |
  | SMTP transport | `smtp.resend.com`, port `465`, user `resend`, pass `env(SUPABASE_SMTP_PASS)` | RD-085 |
  | Email language | **Stacked bilingual** (EN+ES per template) | RD-086 |
  | Templates versioned | invite, recovery, confirmation, magic_link, email_change, security notifications | RD-086 |
  | User ops | invite, list, change_role, resend, disable, revoke, admin_reset | RD-081, RD-082 |
  | Audit | user-mgmt actions → `audit_log` (`actor_id` UUID + `actor_role`, no PII) | RD-089 |
  | CLI pin | Supabase CLI version pinned in `supabase.yml` (template-HTML push, #5686) | RD-088 |
- **Privacy (F15/ADR-026 preserved)**: operator email/role/status are read from Supabase and shown
  in the admin UI **in transit only** — never written to the Vecinita corpus DB. `audit_log` keeps
  only the opaque Supabase UUID + role. Forbidden-table deny-list unchanged.
- **Limitations / scope**: No OAuth/social login; no RBAC beyond `admin`+`viewer`; no MFA/2FA (may be
  a later cycle); no bulk CSV user import; no failed-login lockout beyond Supabase's built-in email
  rate limits; ChatRAG stays anonymous. Supabase serves one template per type (no per-recipient
  locale switching) — hence stacked-bilingual templates.
- **Priority**: High — direct user request (#75 follow-on).
- **Source**: S005 / EV-006 interview 2026-06-29 (RD-080–RD-089; scope addition TP-S005-17–24);
  **S006 / EV-007 delta 2026-06-30** (RD-091–RD-098; F35.12–F35.15; GitHub #109);
  session-brief S005/S006; ADR-029, ADR-031; #75, #109; research (Supabase Admin API + `listUsers` `filter`,
  supabase-js `signOut` scopes, `auth.sessions` revoke, Resend SMTP + REST, supabase-js storage
  adapter, CLI PR #5686 / issue #5124).

### F36: Admin RAG evaluation tab + golden eval set

- **What it does**: Adds an admin-only **Model / RAG Evaluation** tab to the data-management
  frontend so operators run the golden eval set through the production RAG path, view per-metric
  scores (retrieval relevance, faithfulness/groundedness, answer relevancy, latency), drill into
  per-question results, and review run history/trends. Expands the smoke fixture into a maintained
  bilingual golden set with documented curation.
- **Inputs**: Admin operator (`role=admin`); golden fixture `data/fixtures/eval/qa_pairs.json`;
  seeded or staging corpus; Modal self-hosted LLM for LLM-as-judge metrics.
- **Outputs**: Eval run record in Postgres (`eval_runs`, `eval_run_items`); admin UI summary +
  drill-down; CI harness metrics via extended `tests/eval/`.
- **Tooling (R63)**: **LlamaIndex native evaluators** (`FaithfulnessEvaluator`,
  `AnswerRelevancyEvaluator`, optional `ContextRelevancyEvaluator`) + **custom harness**
  (retrieval URL match, latency, Postgres persistence, admin tab). No Langfuse / Ragas / DeepEval
  in v1.
- **Golden set (R67 / RD-099–RD-110)**:
  | Topic | v1 decision |
  |-------|-------------|
  | Domains | Community + housing + legal aid + edge cases |
  | Size | 10 cases, 14 locale rows |
  | es housing/legal | Deferred until #94 adds es corpus docs |
  | Retrieval pass | Expected doc URL in top-k (`retrieval_expectation: hit` / `any_of`) |
  | Answer rubric | `required_facts[]` per row |
  | Edge cases | Abstain, ambiguous query, empty retrieval |
- **Thresholds**:
  | Metric | CI gate | Admin display |
  |--------|---------|---------------|
  | Retrieval relevance | ≥80% on `hit` + `any_of` rows | Same |
  | Faithfulness | ≥0.60 aggregate | Highlight &lt;0.70 |
  | Answer relevancy | ≥0.60 aggregate | Highlight &lt;0.70 |
  | Latency | Informational | p95 per question (30s reference) |
- **Protected surfaces**:
  | Surface | Change |
  |---------|--------|
  | `data-management-frontend` | `/evaluation` route + nav (`admin.nav.evaluation`, en/es) |
  | `internal-write-api` | `POST/GET /internal/v1/eval/runs`, `GET …/{run_id}` |
  | `packages/rag` + Modal | Eval runner job through same RAG path as ChatRAG |
  | `data/fixtures/eval/` | Expanded `qa_pairs.json` + `docs/eval-golden-set.md` runbook |
- **Auth**: **Admin-only** — trigger runs and view results; `viewer` → `403` (RD-110).
- **Privacy**: Fixture-only questions; no visitor PII in eval tables (ADR-004). Judge evaluates
  in query language (RD-109).
- **Coordination**: Align groundedness with #84 when available; primary regression consumer for
  #83 reranking.
- **Limitations / scope**: No public eval UI; no auto prompt tuning; no Langfuse/Phoenix v1; housing/legal
  golden rows en-only until bilingual corpus expands.
- **Priority**: High — GitHub #99 (unblocks tooling decision R63).
- **Source**: S007 / EV-008 interview 2026-07-01 (RD-099–RD-110); context `docs/sessions/S000-internal-docs-archive/context/rag-eval.md`;
  R63, R64, R67; #99, #83, #84, #94.
- **S008 follow-ons (EV-009)**: Optimistic run-list refresh (M65); unified `job_type=eval` on Jobs tab
  (M66); dashboard scatter + time-range presets including custom date picker (M67). Playground and
  promote are **F37** — not extensions of F36 limitations.

### F37: Eval UX polish + playground + runtime config promote

- **What it does**: Closes post-F36 evaluation UX gaps and adds an admin **Playground** tab for
  sandboxed RAG + judge experiments with versioned per-user presets, side-by-side run comparison,
  and super-admin **Promote to production** via a DB-backed active config that ChatRAG reads at
  request time (no redeploy).
- **Inputs**: Admin operator (`role=admin`); super-admin (`role=super-admin`, seeded from
  `VECINITA_SUPER_ADMIN_EMAIL`) for promote; golden fixture and/or ad-hoc question text;
  editable RAG overrides (`top_k`, `min_retrieval_score`, `system_prompt`, `max_tokens`,
  `temperature`, `corpus_profile`, `model_id`); judge criteria selection + judge `temperature`;
  **Ollama model picker** on Modal — list stashed models, background pull job for missing models
  (RD-139–RD-141).
- **Outputs**: Immediate eval run row in history sidebar; eval runs in unified `GET /jobs` with
  `job_type=eval`; enriched dashboard charts; `eval_config_presets` + `eval_runs.config_snapshot`;
  `rag_production_config` active row; promoted config applied to ChatRAG on next ask.
- **Protected surfaces**:
  | Surface | Change |
  |---------|--------|
  | `data-management-frontend` | Optimistic run list; Jobs tab `eval` rows; dashboard chart controls; **Playground** tab (`?tab=playground`); compare view; promote button (super-admin) |
  | `data-management-backend` | Unified jobs list includes `job_type=eval` |
  | `internal-write-api` | Config preset CRUD; eval run create accepts `config` overrides; promote endpoint |
  | `chat-rag-backend` | Read active production config from DB (fallback to env defaults) |
  | `packages/rag` + eval runner | Per-run config override injection (sandbox); Ollama `model_id` routing |
  | Modal Ollama app | Model list API; background pull into `vecinita-models` volume |
- **Auth**: Admin — playground run/view/compare/presets + **list/select Ollama models**; super-admin — promote only; **model pull/download is F38**; viewer → `403`.
- **Privacy**: Ad-hoc operator questions stored in `eval_run_items` with same retention as eval runs
  (ADR-004 — operator content, not visitor PII).
- **Limitations / scope**: Sandbox until promote; no Langfuse/Phoenix; no external Ollama hosts in v1
  (Modal volume only); no in-app redeploy button; guardrails v1 = single `system_prompt` textarea;
  structured guardrail toggles deferred.
- **Milestones**: M65 (run list refresh) → M66 (unified jobs) → M67 (charts) → M68 (config schema +
  presets API) → M69 (playground UI) → M70 (super-admin promote + ChatRAG reader).
- **Source**: S008 / EV-009 interview 2026-07-02 (RD-114–RD-127); context
  `docs/sessions/S000-internal-docs-archive/context/eval-ux-playground.md`; R68–R75.

### F38: Playground model download (super-admin)

- **What it does**: Lets **super-admins** download additional Ollama model tags into the Modal
  `vecinita-models` volume from the Evaluation **Playground** tab so sandbox eval runs can use
  models beyond the default `qwen2.5:1.5b-instruct`. Regular **admins** list and select available
  models for playground runs but cannot trigger pulls.
- **Inputs**: Super-admin operator (`role=super-admin`); free-text Ollama `model_id` tag
  (non-empty, max 128 chars — e.g. `qwen2.5:3b-instruct`); existing Modal Ollama pull
  infrastructure (`POST /models/ollama/pull` on **`vecinita-llm`** — ADR-037; was `vecinita-ollama`).
- **Outputs**: Background Modal pull job (`202` + `job_id`); manifest entry with
  `available: false` while pulling, `available: true` when complete; model appears in Playground
  picker for all admins once available.
- **Protected surfaces**:
  | Surface | Change |
  |---------|--------|
  | `data-management-frontend` | Super-admin-only **Download model** panel on Playground — enter tag, trigger pull, poll list every **10s** for up to **30 min**; hidden for `admin`/`viewer` |
  | `internal-write-api` | Tighten `POST /internal/v1/models/ollama/pull` to `SuperAdminActorDep`; keep `GET /internal/v1/models/ollama` on `WriteActorDep` (admin list) |
  | Modal LLM app (`vecinita-llm`) | **Storage:** `llm-models` volume (`/models`, `manifest.json`); `pull_model_job` via HF Hub (ADR-037) |
- **Storage**: Playground model weights live **only** on Modal Volume **`llm-models`** (not DO disk, Postgres, or S3). Download UI triggers HF Hub staging into this volume; eval/chat read models from the same volume via **`vecinita-llm`** (ADR-037; supersedes ADR-036 `vecinita-models`).
- **Auth**: Super-admin — pull; admin — list + select (no download UI, `403` on pull API); viewer → `403` on all model routes.
- **UX rules**:
  - **Progress**: Poll `GET /internal/v1/models/ollama` until entry `available=true` or **30 min timeout** (then show error; super-admin may retry).
  - **Concurrent pulls**: Allow parallel pull requests for the same tag (duplicate Modal jobs acceptable in v1).
  - **Tag policy**: Free-text Ollama tag; server validates non-empty + length only (no allow-list v1).
- **Limitations / scope**: Pull UI only — no Ollama library catalog browser; no auto-pull on eval run when model missing; requires `VECINITA_MODAL_LLM_URL` configured (deploy prerequisite).
- **Milestones**: M71 (API auth: super-admin-only pull) → M72 (Playground download UI + poll) → M73 (full-stack tests).
- **Source**: S009 / EV-010 interview 2026-07-05 (RD-142–RD-148); context
  `docs/sessions/S000-internal-docs-archive/context/playground-model-download.md`; supersedes TC-134 admin-pull expectation from F37.
- **Backend note (F39/ADR-037)**: UI and internal-write-api paths unchanged (`/internal/v1/models/ollama/*`); Modal backend is **`vecinita-llm`** with HF downloads, not `ollama pull`.

### F39: Unified LLM Modal service (deprecate `vecinita-ollama`)

- **What it does**: Consolidates all Modal LLM responsibilities onto **`vecinita-llm`**: vLLM inference
  (`/generate`, `/warm`), playground model list/pull (`/models/ollama`), and weight staging
  (`stage_llm_weights`, `stage_default_model`, `pull_model_job`). Deprecates and de-deploys
  **`vecinita-ollama`**.
- **Inputs**: Existing `VECINITA_MODAL_LLM_URL` + `VECINITA_MODAL_PROXY_KEY`; optional `model_id`
  on generate/warm (Ollama-style tags resolved via `llm_model_registry.py` → HuggingFace repos).
- **Outputs**: Single Modal ASGI URL for ChatRAG, ingest/retag, eval, and playground; manifest on
  **`llm-models`** volume at `/models/manifest.json`.
- **Protected surfaces**:
  | Surface | Change |
  |---------|--------|
  | `infra/modal/llm_app.py` | Add `pull_model_job`, `stage_default_model`, `/models/ollama` routes; HF Hub download |
  | `packages/llm-client` | Route all HTTP to `VECINITA_MODAL_LLM_URL`; drop Ollama URL branch |
  | `packages/eval` | `eval_runtime_for_config` always uses `vecinita-llm` + sandbox `model_id` |
  | `chat-rag-backend` | Prefer LLM URL only (remove Ollama URL preference) |
  | `internal-write-api` | `OllamaModelsClient` targets `vecinita-llm` routes |
  | `scripts/deploy/modal.sh` | Deploy `llm_app` only; remove `ollama_app` |
- **Technical constraints (ADR-037)**:
  - vLLM cannot read Ollama blob cache — downloads use **`huggingface_hub.snapshot_download`**, not `ollama pull`.
  - One active vLLM model per GPU instance; tag switch reloads engine (~60–120s); `/warm` accepts `model_id`.
  - Legacy `vecinita-models` Ollama blobs are **not** migrated — re-stage via HF.
- **Env deprecation**: `VECINITA_MODAL_OLLAMA_URL` removed from DO specs; clients may warn if still set.
- **Auth**: Unchanged — proxy key on Modal model routes; admin JWT on internal-write-api.
- **Milestones**: M74 (extend `llm_app` + registry) → M75 (rewire clients + eval) → M76 (deploy smoke + de-deploy ollama).
- **Source**: S010 / EV-011 2026-07-08 (RD-154–RD-162); ADR-037; context
  `docs/sessions/S010-unify-llm-service/context-brief.md`.

#### F39 follow-on — client consolidation (2026-07-10, RD-163–RD-172)

Same feature ID (**F39**); no F40. Cleanup after ADR-037 — **not** a multi-provider framework.

| Slice | Scope | User-visible? |
|-------|--------|---------------|
| **A** (first) | One `LlmClient` surface (merge generate/stream/warm + list/pull) + rename Ollama modules/types → playground; keep `/models/ollama` path aliases | Mostly internal |
| **B** | Real vLLM token SSE streaming; `VECINITA_MODAL_PROXY_KEY` required on `/generate`, `/warm`, `/models/*` (`/health` may stay open) | Live tokens; 401 without key |
| **C** | Shared HF `apply_chat_template` helper; catalog/list/pull gated by `resolve_hf_repo` | Better non-Qwen prompts; clear unmapped errors |
| **D** | Separate playground Modal class; prod pinned to `qwen2.5:1.5b-instruct` / `Qwen/Qwen2.5-1.5B-Instruct` | Playground reload does not stomp ChatRAG |
| **E** | Drop legacy `VECINITA_MODAL_OLLAMA_URL` / `VECINITA_OLLAMA_MODEL_ID` fallbacks; fix package docs; declare `shared-schemas` on `llm-client` | Operator/docs |

**Out of scope:** Provider ABC / second backend (SaaS, llama.cpp, Ollama runtime); mandatory FE path rename away from `/models/ollama`.

**Source:** S010 seed `checkpoints/01-requirements-seed.md`; interview Q1–Q3 approve-all 2026-07-10.

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
