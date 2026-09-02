# Feature List

> **Project**: Vecinita  
> **Repository**: `/root/GitHub/VECINA/vecinita`  
> **Last updated**: 2026-08-29 (EV-036 F84 monitoring + staging Grafana/Loki #114)
> **Source**: Standing product specs + evolve deltas; cite [ADR index](adr/README.md) and session decision logs for cycle history.

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
| F9 | Corpus list / delete (admin) | Implemented (+ EV-013 polish) | Data Management | data-management-backend, data-management-frontend | 11-verify-impl 2026-05-19; EV-013 #148 density/truncation |
| F10 | Multilingual 384-d embeddings on Modal | Implemented (via F70) | Data Management / Cross-cutting | Modal embed, embedding-client | S027 #159; was FastEmbed-en |
| F11 | ChatRAG web UI (React/Vite) | Implemented | ChatRAG | chat-rag-frontend | Vitest smoke; UI E2E waived v1 |
| F12 | Data management admin UI | Implemented (+ EV-013 polish) | Data Management | data-management-frontend | Vitest smoke; EV-013 #148 shared table density |
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
| F31 | Admin + shared frontend bilingual UI (en/es) | Implemented | Cross-cutting | data-management-frontend, chat-rag-frontend, `packages/frontend-i18n`, `packages/frontend-ui` | Shared packages shipped |
| F32 | Admin Job Management tab (list jobs) | Implemented → Evolving (EV-012) | Data Management | data-management-backend, data-management-frontend | S002 2026-06-26 (#89); S013/EV-012 #116 |
| F33 | Browser-local persistent chat history (localStorage + previous-chats list) | Planned | ChatRAG | chat-rag-frontend | S003 2026-06-26; ADR-025 2026-06-28 |
| F34 | Supabase Auth for admin surfaces (invite-only, admin+viewer) | Planned | Cross-cutting (admin) | data-management-frontend, data-management-backend, internal-write-api | S004/EV-005 2026-06-28; ADR-026 (#75) |
| F35 | Admin user management + remember-me + Resend SMTP/templates | Planned | Cross-cutting (admin) | data-management-frontend, data-management-backend, supabase config + CI | S005/EV-006 2026-06-29; ADR-029 (#75) |
| F36 | Admin RAG evaluation tab + golden eval set | Implemented → Evolving (EV-012) | Data Management | data-management-frontend, internal-write-api, packages/eval, data-management-backend (Modal jobs) | S007/EV-008 2026-07-01; #99; S013/EV-012 #116 Modal job lifecycle |
| F37 | Eval UX polish + playground + runtime config promote | Planned | Data Management + ChatRAG | data-management-frontend, internal-write-api, data-management-backend, chat-rag-backend | S008/EV-009 2026-07-02 |
| F38 | Playground model download (super-admin) | Implemented | Data Management | data-management-frontend, internal-write-api, Modal LLM app | S009/EV-010 2026-07-05; backend unified in F39 |
| F39 | Unified LLM Modal service (deprecate `vecinita-ollama`) | Planned | Cross-cutting | `infra/modal/llm_app.py`, `packages/llm-client`, all LLM consumers | S010/EV-011; ADR-037; follow-on RD-163–RD-172 |
| F40 | ChatRAG cold-start wait UX (rotating fun facts + consent) | Planned | ChatRAG | chat-rag-frontend; optional `frontend-i18n` / `frontend-ui` | S016/EV-014 #87 |
| F41 | Corpus re-embed / re-chunk rebuild (migration job) | Planned | Data Management | data-management-backend, internal-write-api, data-management-frontend, Modal | S017/EV-015 #167 |
| F42 | Richer context packing + multi-query retrieval (H7+P1) | Implemented | ChatRAG | packages/rag, chat-rag-backend; F36 eval sandbox join | S019/EV-016 #165; PR #172 |
| F43 | Answer / retrieval cache (H1 cascade) | Planned | ChatRAG | packages/rag, chat-rag-backend; F36 harness | S020/EV-017; S020-D4/D7 |
| F44 | Soft language filter / empty-hit fallback (#162) | Planned | ChatRAG | packages/rag, chat-rag-backend | S020/EV-017 #162; S020-D6/D7 |
| F45 | Cross-encoder rerank spike + gated ship (#83/#161) | Implemented | ChatRAG | packages/rag, rerank-client, chat-rag-backend; Modal `vecinita-rerank` | 11-verify-impl EV-029 2026-08-24; staging CE on |
| F81 | LLM query refinement before retrieval (#82) | Implemented | ChatRAG | packages/rag, chat-rag-backend, llm-client | 11-verify-impl EV-029 2026-08-24; flag default-off; staging enable deferred |
| F82 | Output verification + inline citations (#84) | Implemented (live) | ChatRAG | packages/rag, chat-rag-backend, packages/eval | EV-030 live verify 2026-08-24 |
| F46 | Staging retrieve reliability (non-empty pools) | Planned | ChatRAG | packages/rag, chat-rag-backend, database/corpus pin | S021/EV-018; S021-D8 |
| F47 | Skip re-ingest when content_hash unchanged (#163) | Implemented | Data Management | data-management-backend, internal-write-api, packages/ingest | 11-verify-impl S022 2026-08-02; EV-019 #163 |
| F48 | Embedding sub-batch + retry for ingest (#166) | Implemented | Data Management | packages/embedding-client, data-management-backend, Modal embed | 11-verify-impl S022 2026-08-02; EV-019 #166 |
| F49 | Chunk overlap + sizing clarity (#160) | Implemented | Data Management | packages/ingest, config-spec; optional admin FE | 11-verify-impl S022 2026-08-02; EV-019 #160 |
| F50 | Promote prod top_k to 8 (#158) | Implemented | ChatRAG | packages/rag, chat-rag-backend, config-spec, DO env | S023/EV-020 #158 |
| F51 | Default P3 context packing (#165) | Implemented | ChatRAG | packages/rag, chat-rag-backend, config-spec, DO env | S023/EV-020 #165 |
| F59 | Robust scrape (main-content, politeness, JS-render, PDF text) (#69) | Planned | Data Management | packages/ingest, data-management-backend, Modal | S024/EV-022 #69 |
| F60 | Website crawl from seed URL (#71) | Planned | Data Management | packages/ingest, data-management-backend, DM frontend, Modal | S024/EV-022 #71 |
| F61 | Corpus tree UI + nested source metadata (#70) | Planned | Data Management (+ ChatRAG backend meta) | data-management-frontend, DM backend, write API, chat-rag-backend | S024/EV-022 #70 |
| F62 | Husky lean pre-push + expanded pre-commit (#182) | Planned | Cross-cutting (infra) | `.husky/`, `scripts/ci/`, Makefile, LOCAL_DEV, ci-local-parity | S025/EV-023 #182 |
| F63 | Automate release tagging after main CD (#103) | Planned | Cross-cutting (infra) | `.github/workflows/`, deploy docs, CHANGELOG alignment | S025/EV-023 #103 |
| F64 | Cold-start wait: query tips + VECINA marketing | Implemented | ChatRAG | chat-rag-frontend | S026/EV-024 #87/#193 |
| F65 | Ask energy estimate + use guide + advisory | Implemented | ChatRAG | chat-rag-backend, chat-rag-frontend | S026/EV-024 #93/#193 |
| F66 | Action icon micro-interactions | Implemented | Cross-cutting | `frontend-ui`, both frontends | S026/EV-024 #104/#193 |
| F67 | Bilingual tooltips / contextual hints | Implemented | Cross-cutting | `frontend-ui`, `frontend-i18n`, both frontends | S026/EV-024 #106/#193 |
| F68 | ChatRAG feedback page + backend (anonymous) | Implemented | ChatRAG + Admin | chat-rag-*, internal-write, database, admin FE | S026/EV-024 #186/#193 |
| F69 | Admin audit actor username (read-time) | Implemented | Data Management | data-management-backend/frontend | S026/EV-024 #170/#193 |
| F70 | Multilingual embedding runtime + model pin | Implemented | Cross-cutting | Modal embed, `packages/embedding-client`, ChatRAG + ingest | S027/EV-025 #159 |
| F71 | Corpus re-embed + prod cutover (multilingual pin) | Implemented | Data Management | F41 rebuild/promote, Modal, internal-write, Admin Jobs | S027/EV-025 #159 |
| F72 | Citation UI — validate URLs before href | Implemented | ChatRAG | chat-rag-frontend `SourceList` | S028/EV-026 #222 |
| F73 | Dynamic relevance-gated sources (no fixed pad) | Implemented | ChatRAG | packages/rag, chat-rag-backend | S028/EV-026 #223 |
| F74 | Operator-settable `display_title` | Implemented | Data Management + ChatRAG | internal-write, DB migration, admin FE, citation packing | S028/EV-026 #224 |
| F75 | Optional ingest bilingual translation | Implemented | Data Management | data-management-backend, internal-write-api, Modal LLM, admin FE | EV-030 #251 |
| F76 | Corpus language parity metrics + badges | Implemented | Data Management | internal-write-api, data-management-frontend | EV-031 #245 |
| F78 | Corpus change automations | Live enabled (EV-031) | Data Management / infra | Modal DM, DM backend/FE, internal-write | S030 #73; EV-031 M133/M135 |
| F79 | Corpus freshness automation | Live enabled (EV-031) | Data Management / admin | Modal schedule, ingest, DM FE, write API | S030 #219; EV-031 M133 |
| F80 | Modal LoRA fine-tune + human promote | Eval path live (EV-031); prod promote deferred | Cross-cutting (LLM) | finetune_app.py, llm_app, llm-client, eval, admin FE | S030 #72; EV-031 M134 |
| F83 | Distinct staging environment (DO + Supabase + Modal) | Implemented | Cross-cutting (infra) | DO apps/DB, Supabase project, Modal Environment `staging` (workspace `vecinita`), GH Environments + ruleset + Stage→Main agent rule | EV-staging-do-supabase; EV-033; ADR-054 |
| F84 | Admin monitoring dashboard + staging Grafana/Loki/alerts | Planned | Data Management / infra | internal-write-api, chat-rag-backend, DM frontend, database, `infra/observability/` | EV-036 #114; ADR-055 |

**Status key**: Implemented = production-ready / shipped in tree, In progress = actively building this cycle, Planned = not yet built, Experimental = works but not validated

## Feature Details

### F1: Bilingual community Q&A (RAG chat)

- **What it does**: Answers community questions in English or Spanish using retrieved corpus context and a self-hosted LLM.
- **Inputs**: User question (text); optional language hint from client; corpus in Postgres/pgvector.
- **Outputs**: Answer text (and streamed tokens when streaming enabled).
- **Key parameters**:
  | Parameter | Default | Range | Description |
  |-----------|---------|-------|-------------|
  | `top_k` | `8` (`VECINITA_TOP_K`) | 1–50 | Max retrieved chunks per query (F50; F73 upper bound — not a pad target; was 5) |
  | `chunk_size` | `256` tokens (`VECINITA_CHUNK_SIZE_TOKENS`) | ≥ 64 | Chunk size at ingest (HF tokenizer; F49) |
  | `chunk_overlap` | `32` tokens (`VECINITA_CHUNK_OVERLAP_TOKENS`) | 0 … &lt; size | Overlap between chunks (F49 / ADR-044) |
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
- **Limitations**: Public HTML/text scrape; PDF via F59. **Google Drive / Docs (#235):**
  public file / Docs / Sheets share links rewrite to export/download; auth/loading shells
  (`Loading… Sign in`) fail with `drive_auth_required` and are **not** upserted. Private,
  folder-only, and login-required links are unsupported — upload the file or paste an export
  URL. Multi-URL ingest soft-fails per URL with a browser-like User-Agent (#243).
  Apex hosts with broken TLS may retry `www.` (#249). Persistent `403` from
  datacenter IPs surfaces `host_waf_blocked`; TLS without recovery surfaces
  `tls_handshake_failed` (operator-visible in job metrics).
- **Source**: User interview 01-requirements; #235 / #243

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
- **EV-013 / #148 polish (S014)**: Dense single-screen corpus table — keep server pagination (`page_size` 50 from #112); sticky header; compact rows; truncate long titles/URLs with ellipsis; full text via native `title` + `aria-label` (no Tooltip required); bound tag chips (`+N`); Actions column stays visible without horizontal page scroll on ~1280×800. Empty/loading/error states unchanged. **Privacy**: truncation chrome uses **no cookies** and **no new `localStorage` keys**; theme stays on existing device-local `vecinita-ui-theme` only; OS `prefers-contrast: more` / `contrast-more:` CSS only (no high-contrast toggle, no tracking).

### F10: Multilingual 384-d embeddings on Modal

- **What it does**: Batch/single embed HTTP on Modal (`/embed`, `/embed/batch`) producing
  **384-d** vectors for ingest and ChatRAG query. **EV-025 / ADR-048:** hosts the shared
  multilingual pin (planned candidate E1 `intfloat/multilingual-e5-small`; final after F36
  operator review). Runtime prefers **FastEmbed**; allows **sentence-transformers** or
  **custom ONNX** when FastEmbed cannot load the winner (S027-D12). Shared
  `packages/embedding-client` applies e5 `query:` / `passage:` prefixes when required.
  Historical v1 ship used English-only `BAAI/bge-small-en-v1.5` via FastEmbed (ADR-008,
  superseded). Detailed cutover + rechunk lives in **F70/F71**; F10 is the embed **service**
  capability row.
- **Inputs**: Text or batch of texts; query vs passage mode; model id / runtime config.
- **Outputs**: 384-dimensional vectors; health/model metadata.
- **Limitations**: Modal pay-per-invoke; `vector(384)` schema (dim change needs new ADR);
  weights on Modal volume / image — not in Vecinita DB.
- **Protected surfaces**: `infra/modal/embedding_app.py`; `packages/embedding-client`.
- **Source**: User interview; R8; S027/EV-025; ADR-048; F70.
- **Status**: Implemented (F70 pin in code; 11-verify-impl S027-D47; prior FastEmbed-en path superseded).

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
- **EV-013 / #148 polish (S014)**: Shared truncation/density helpers applied to Jobs, Users, Audit, and Evaluation list tables (same patterns as F9 Corpus). Theme-aware via existing `ThemeProvider` light/dark/system + semantic Tailwind tokens; readable under OS high-contrast (`prefers-contrast`). Must not introduce cookies, consent banners, or new preference storage beyond existing keys (`vecinita-ui-theme`, `vecinita.locale`, auth remember — unchanged).

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
- **ChatRAG catalog ownership (EV-296 / #296)**: Visitor-facing UI strings live in `packages/frontend-i18n` under **`chat.<camelCase>`** (plus existing `chat.tooltip.*`). ChatRAG must not keep a divergent local string table for moved keys; call sites use package `t(locale, "chat.*")`. Pagination uses `shared.pagination`. Cold-start **facts** may remain in `apps/chat-rag-frontend/src/coldstart/facts.ts` until a separate decision. Staff copy-change path: [runbooks/staff-copy-change.md](runbooks/staff-copy-change.md) (`[Corpus: staff-copy]`, #297).
- **Limitations**: UI chrome only — corpus document titles, tag labels, URLs, audit JSON payloads, API `error_message`, and health/job status enums remain in source form (R30). No backend or API contract changes. No `Accept-Language` header in F31.
- **Priority**: High — ship in EV-004 before next deploy.
- **Source**: EV-004 user interview 2026-06-13; ADR-019, ADR-020 (amended); context-brief §13; EV-037-D2 / EV-296 (#296)

### F32: Admin Job Management tab (list jobs)

- **What it does**: Adds a Job Management tab to the admin dashboard that lists all ingest/retag jobs (running, completed, failed) sourced from a new server-backed list endpoint. Because job state is read from the server (not component-local React state), switching tabs and returning no longer drops running/failed job info (the original symptom in #89; same class as #53).
- **Inputs**: Operator browser; `GET /jobs` on the data-management backend (optional `?status=` filter).
- **Outputs**: Table of jobs with short job id, type (ingest/retag), status badge, source URLs, last-updated time, and `error_code: error_message` for failed jobs; polled while open; manual refresh.
- **Backend**: `GET /jobs` list endpoint (newest first) + `list_jobs()` on `JobStore` / `DictJobStore` / `InMemoryJobStore`; `job_type` added to the `Job` schema; `JobList` response model; OpenAPI `openapi/data-management.yaml` updated.
- **Frontend**: New `/jobs` route + sidebar nav item (`ListChecks`); `JobsPage`; `listJobs()` client; en/es i18n (`admin.nav.jobs`, `admin.jobs.*`).
- **Limitations**: No PII in listings (URLs + status only, ADR-004). Status/type enums localized; error messages remain in source form (consistent with F31 R30). **Superseded by EV-012:** cancellation/retry/delete are in scope (RD-176); list updates use SSE + poll fallback (RD-173).
- **Priority**: High — pairs with #88 ingest tag resilience.
- **Source**: S002 session (GitHub #89); related bug #88 (graceful ingest tagging).
- **EV-012 / #116 delta (S013, RD-173–RD-178)**: Unified long-running job monitoring on Admin Jobs only (not ChatRAG).
  - **Lifecycle**: All long-running admin jobs (ingest, retag, **eval**, future types) use **Modal’s job lifecycle** ([Modal job queue](https://modal.com/docs/guide/job-queue)); Admin Jobs list is **Modal `GET /jobs`** with extensible `job_type` (RD-174). Amends ADR-033 (eval leaves DO `BackgroundTasks`).
  - **Storage**: **DO Postgres** remains SoT for durable storage including eval metrics/results; **Supabase = authentication only** (RD-175).
  - **UX**: Status filter UI; clickable rows → `/jobs/:id` detail (`JobDetailPage`); retag shows `document_id` context; SSE on Modal jobs **and** internal-write eval progress with **4s poll fallback** + SSE retry backoff (RD-173, 02-verify M2); failed Modal jobs show function/call id + copy + dashboard link when known (RD-177); admin cancel/retry/delete (RD-176).
  - **CRUD**: **Admin-only** full job CRUD — create (existing), read/list/detail, cancel/retry, delete from store (RD-176). Viewer read-only.
  - **Tests**: Extend UJ-023; UJ-050 detail; Playwright T0-ui list→detail (RD-178); API e2e + Vitest; live T3 after deploy.

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
- **EV-012 / #116 delta (S013, RD-174–RD-175)**: Eval **run lifecycle** moves to Modal
  (`job_type=eval` on data-management jobs API; Modal job queue). Trigger may still originate from
  `/evaluation` / internal-write, but the async job is owned by Modal. **Postgres** keeps
  `eval_runs` / `eval_run_items` (metrics, per-row results) as storage SoT. Jobs tab shows eval via
  Modal list; detail summary links to existing eval drill-down (`/evaluation?run=…`). Amends
  ADR-033 runner placement.

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
  (non-empty, max 128 chars — e.g. `qwen2.5:1.5b-instruct`); existing Modal Ollama pull
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
  | `packages/llm-client` | Single `LlmClient` (generate/stream/warm + list/pull); drop Ollama URL branch |
  | `packages/eval` | `eval_runtime_for_config` always uses `vecinita-llm` + sandbox `model_id` |
  | `chat-rag-backend` | Prefer LLM URL only (remove Ollama URL preference) |
  | `internal-write-api` | Playground library client targets `vecinita-llm` `/models/ollama*` aliases |
  | `data-management-frontend` | `playground_*` API helpers + UI copy; paths stay `/internal/v1/models/ollama*` |
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

Same feature ID (**F39**); follow-on did not allocate a new Fn (F40 later used for ChatRAG
cold-start UX in EV-014). Cleanup after ADR-037 — **not** a multi-provider framework.

| Slice | Scope | User-visible? |
|-------|--------|---------------|
| **A** (first) | One `LlmClient` surface (merge generate/stream/warm + list/pull) + rename Ollama modules/types → playground; keep `/models/ollama` path aliases | Mostly internal; FE UI copy → Playground (paths unchanged) |
| **B** | Real vLLM token SSE streaming; `VECINITA_MODAL_PROXY_KEY` required on `/generate`, `/warm`, `/models/*` (`/health` may stay open) | Live tokens; 401 without key |
| **C** | Shared HF `apply_chat_template` helper; catalog/list/pull gated by `resolve_hf_repo` | Better non-Qwen prompts; clear unmapped errors |
| **D** | Separate playground Modal class; prod pinned to `qwen2.5:1.5b-instruct` / `Qwen/Qwen2.5-1.5B-Instruct` | Playground reload does not stomp ChatRAG |
| **E** | Drop legacy `VECINITA_MODAL_OLLAMA_URL` / `VECINITA_OLLAMA_MODEL_ID` fallbacks; fix package docs; declare `shared-schemas` on `llm-client` | Operator/docs |

**Out of scope:** Provider ABC / second backend (SaaS, llama.cpp, Ollama runtime); mandatory FE path rename away from `/models/ollama`.

**Slice A rename lock (M77 / RD-166):** Types and modules are `playground_*` /
`PlaygroundModel*` / `fetchPlaygroundModels` / `LlmClient.list_models|start_pull`. HTTP aliases
remain `/models/ollama*` and `/internal/v1/models/ollama*`. `OllamaModelsClient` is deleted.

**Source:** S010 seed `checkpoints/01-requirements-seed.md`; interview Q1–Q3 approve-all 2026-07-10.

### F40: ChatRAG cold-start wait UX (rotating fun facts + consent)

- **What it does**: During ChatRAG cold-start retries or slow first-token waits (>8s), show
  rotating bilingual (EN/ES) WRWC / Providence / ways-to-give fun facts plus a short
  “starting up…” status line, a soft donate CTA (`wrwc.org/donate`), and a friendly
  first-party consent banner before remembering which facts were shown (opt-out via HTTP
  cookie). Extends existing `coldStartStatus` / `prewarmChatServices` client warm —
  residual wait UX when prewarm loses the race (create/clean boot / cold restore).
- **Inputs**: Locale; cold-start retry / stream timing; optional `VITE_WRWC_DONATE_URL`
  (default `https://wrwc.org/donate/`); consent choice; seen-fact ids in `localStorage`.
- **Outputs**: Improved wait UX; device-local preference cookie + seen-facts list (no PII,
  not required by ChatRAG APIs).
- **Protected surfaces**:
  | Surface | Change |
  |---------|--------|
  | `apps/chat-rag-frontend` | Rotating facts UI, consent banner, donate CTA, warm reuse |
  | `packages/frontend-i18n` / `frontend-ui` | Optional shared banner/copy if needed |
- **Related (not F40 UX)**: EV-318 / #318 — Modal LLM `POST /warm` spawn/detach + ChatRAG
  `POST /api/v1/warm` contract (ADR-022 prewarm lever). F40 does **not** own that work.
- **Out of scope (F40)**: Changing Modal spawn semantics (see #318); CMS/API-backed facts;
  admin UI; analytics of which facts were shown; focus/typing warm predictors.
- **Source**: S016 / EV-014; GitHub #87; Phase 0 intake 2026-07-29 (S016-D1–D15);
  EV-318 coord 2026-09-02.

### F41: Corpus re-embed / re-chunk rebuild (migration job)

- **What it does**: Safe, repeatable corpus rebuild plus a **Postgres document store**
  (normalized body + revisions) so operators can re-embed / re-chunk / rescrape without
  ad-hoc SQL. Modes: **`reembed`**, **`rechunk`**, **`rescrape`** via single
  `job_type=rebuild`. EV-015 staging ops prefer **store-backed** reembed/rechunk (**no live
  scrape** unless explicit rescrape). Dry-run uses **shadow dual-write**; **F36 against
  shadow before promote**. **Version stamps** track embedding model/dim, chunk settings, and
  `rebuild_run_id` across revisions. **force** bypasses content_hash skip (#163). Includes
  **one-time backfill** of existing corpus into `body_text` / revisions. Prod cutover =
  runbook only.
- **Inputs**: `mode`; optional `document_ids`; `force`; `dry_run`; current chunk/embed settings.
- **Outputs**: Store body/revisions (incl. backfill); shadow or live chunks/embeddings; Jobs
  progress; Admin promote; version stamps; #159–#166 dependency checklist; staging→prod
  runbook outline.
- **Protected surfaces**:
  | Surface | Change |
  |---------|--------|
  | `apps/database` | Migration: body_text, document_revisions, shadow/rebuild metadata |
  | `apps/internal-write-api` | Store upsert + rebuild promote paths |
  | `apps/data-management-backend` | Rebuild pipeline; ingest writes store; **backfill** job/path |
  | `apps/data-management-frontend` | Jobs UI: enqueue rebuild (mode/force/dry-run) + **promote** |
  | Modal data-management | Long-running rebuild worker |
- **Out of scope (this cycle)**: Live prod rebuild; chunk overlap values (#160); dual-write
  dim migration impl; retag-inside-rebuild; new % widget.
  **Note:** Multilingual model pick (#159) moved to **S027/EV-025 F70–F71** (no longer OOS).
- **Source**: S017 / EV-015; GitHub #167; ADR-040; intake 2026-07-30 (S017-D1–D17);
  02-verify-plan M1–M4 (2026-07-30).

### F42: Richer context packing + multi-query retrieval (H7+P1)

- **What it does**: Ships the EV-016 hybrid winner **Hy1 = H7+P1 on E0** (`BAAI/bge-small-en-v1.5`).
  **P1** formats each retrieved chunk as `Source: {title}\nURL: {url}\n{text}`. **H7** runs a
  thin multi-query fan-out (2–3 **cheap heuristic** rewrites — not LLM; Spanish-aware for `es`),
  merges/dedupes by chunk id / score, then packs. Shared helpers in `packages/rag`; ChatRAG `_build_prompt` and F36 eval
  sandbox use the same path. Optional **P3** (document dedupe + char budget) shipped
  config-gated in EV-016; **F51 (EV-020)** promotes P3 to the prod default.
- **Inputs**: Query text + locale; existing retrieval (`top_k`, `min_retrieval_score`); optional
  packer / H7 config flags.
- **Outputs**: Packed context string for synthesis; same citation/source surfaces as today;
  F36 Hy1 metrics on staging golden (ISS-008 fixture path required for promote smoke).
- **Protected surfaces**:
  | Surface | Change |
  |---------|--------|
  | `packages/rag` | Shared P1 packer + thin H7 fan-out helpers |
  | `apps/chat-rag-backend` | Wire `_build_prompt` / retrieve path through shared helpers |
  | F36 eval sandbox | Same packing + H7 as ChatRAG (no parallel prompt assembly) |
- **Out of scope (EV-016)**: Multilingual embed swap / #159 / E1 promote; R1 cheap rerank;
  CE/#83; soft language filter #162; LangGraph / ADR-006 amend; answer cache (→ F43 in EV-017);
  model upsizing; changing prod embed pin.
- **Ship prereq**: ISS-008 write-api deploy so Admin `corpus_profile=staging` loads
  `qa_pairs_staging.json` before promote-path smoke.
- **Source**: S019 / EV-016; GitHub #165; harness H7; S019-D22/D31/D37; hybrid
  `20260801T002819Z_hybrid-sweep.json`; E1 reject `20260801T130441Z_e1-shadow-f36.json`;
  PR #172 @ `b08ec30`.
- **Follow-on**: F50 (`top_k=8`) + F51 (default P3) in EV-020 / S023.

### F50: Promote prod top_k to 8 (#158)

- **What it does**: Changes the production retrieval default from **`top_k=5` → `8`** so ChatRAG
  returns up to eight sources per ask (retrieve count = sources shown; no separate FE cap).
  Aligns code default (`DEFAULT_TOP_K` / settings), `infra/vecinita.yaml`, config-spec, and
  DO `VECINITA_TOP_K` (deploy Path A). Reuses S019 A1 spike evidence; not a new investigation.
- **Inputs**: Existing ask/stream path; `VECINITA_TOP_K` / settings `top_k`.
- **Outputs**: Up to 8 `sources[]` when corpus has enough hits above `min_retrieval_score`.
- **Protected surfaces**:
  | Surface | Change |
  |---------|--------|
  | `packages/rag` | `DEFAULT_TOP_K = 8` |
  | `apps/chat-rag-backend` | Settings default `VECINITA_TOP_K=8` |
  | `infra/do/chat-rag-backend.yaml` + DO app env | `VECINITA_TOP_K=8` |
  | `infra/vecinita.yaml` / config-spec | Document default 8 |
- **Out of scope (EV-020)**: Adaptive top_k; retrieve-N-show-K UI truncation; CE enable (#83).
- **Source**: S023 / EV-020; GitHub #158; S019 A1; S023-D6.

### F51: Default P3 context packing (#165)

- **What it does**: Promotes **`VECINITA_RAG_PACKER` default from `p1` → `p3`** so prod packing
  runs document_id dedupe + char budget (`VECINITA_RAG_CONTEXT_MAX_CHARS=3500` unchanged)
  after P1 Source/URL headers. Code path already exists (`pack_chunks(mode="p3")`); this cycle
  flips defaults + tests + DO env. Closes the residual of #165 after F42 shipped P1.
- **Inputs**: Retrieved chunks; packer mode + max_chars settings.
- **Outputs**: Packed prompt context with ≤1 chunk per `document_id` (highest score) and
  prefix-truncated to budget; same ask response shape.
- **Protected surfaces**:
  | Surface | Change |
  |---------|--------|
  | `apps/chat-rag-backend` | Default `rag_packer="p3"` |
  | `infra/do` / DO ChatRAG env | `VECINITA_RAG_PACKER=p3` (add if absent) |
  | config-spec / vecinita.yaml | Default `p3` |
  | F36 eval sandbox | Inherit same default via shared settings helpers |
- **Out of scope (EV-020)**: Token-accurate budget (char budget stays); new packer modes; H7 redesign.
- **Source**: S023 / EV-020; GitHub #165; S019 A2 / F42; S023-D6.

### F43: Answer / retrieval cache (H1 cascade)

- **What it does**: Cuts LLM cost/latency on repeat asks via a **full H1 cascade** (S020-D4):
  (1) exact answer cache on normalized query+locale → (2) semantic answer cache (cosine
  threshold) → (3) retrieve-result cache → (4) generate + store. Shared helper in
  `packages/rag`; ChatRAG ask/stream wires the cascade. **No LangGraph** (ADR-006 unchanged).
  Keys are content-hash only (ADR-004 — no identity/session keys).
- **Inputs**: Normalized query + locale; optional cache config (TTL, max entries, semantic
  threshold); corpus/version stamp for invalidation.
- **Outputs**: Cached or freshly generated answer + sources; observability for
  `cache_hit` ∈ {none, exact, semantic, retrieve}; F36/harness cost + hit-rate cells.
- **Protected surfaces**:
  | Surface | Change |
  |---------|--------|
  | `packages/rag` | Normalize + cascade lookup/store helpers |
  | `apps/chat-rag-backend` | Wire ask/stream through cascade before/after retrieve+synth |
  | F36 / eval harness | Warm/cold cost + quality ≥ H0 gates |
- **Out of scope (this cycle)**: Modal volume durable cache (unless 01 unlocks); LangGraph;
  identity-keyed memory; changing synthesizer pin.
- **Source**: S020 / EV-017; S019 harness H1/H9; S020-D4/D7/D8.

### F44: Soft language filter / empty-hit fallback (#162)

- **What it does**: When same-language retrieve returns **empty** (above min_score), optionally
  retry without language filter (**L1**). Shipped **config-gated, default off** (S020-D6) so
  prod behavior stays L0-strict until enabled. Includes an **empty-hit fixture** so the path
  is testable (staging golden alone never fired soft fallbacks).
- **Inputs**: Query + detected locale; flag e.g. `VECINITA_RAG_SOFT_LANGUAGE_FALLBACK`;
  existing `min_retrieval_score` / `top_k`.
- **Outputs**: Chunks from same-lang pass or fallback pass; metrics for fallback fired /
  empty_final; no change to answer schema.
- **Protected surfaces**:
  | Surface | Change |
  |---------|--------|
  | `packages/rag` | L1 retrieve helper (same-lang then optional unfiltered retry) |
  | `apps/chat-rag-backend` | Flag-gated wire on retrieve path |
  | tests / fixtures | Empty-hit fixture + unit/e2e coverage |
- **Out of scope (this cycle)**: L2 opposite-language-only; changing default-on without evidence.
  (#159 embed swap moved to EV-025 F70–F71.)
- **Source**: S020 / EV-017; GitHub #162; S019 A3 spike; S020-D6/D7/D8.
- **Follow-on (EV-025)**: F71 may retune flag/thresholds only if post–multilingual-pin F36
  shows ES/lang-filter harm (S027-D19/D20); no separate F72.

### F45: Cross-encoder rerank spike + gated ship (#83/#161)

- **What it does**: **Cross-encoder rerank** for smart retrieval: retrieve-N → CE score →
  keep `top_k` (F73 threshold-aware). Spike gate **PASS** (S021 AC-BB9). EV-029 ships production
  Modal app `vecinita-rerank`, HTTP client, and ChatRAG wiring; enables on **staging** first.
  Prod `VECINITA_RAG_RERANK_CE` stays **false** until deploy AskQuestion (AC-FO4).
- **Model**: **`BAAI/bge-reranker-v2-m3`** on Modal T4 (RD-213). Prior R3 (`bge-reranker-base`)
  failed lift — do not regress model choice.
- **EV-017 outcome**: Path A ship gate **FAIL** on empty pools (S020-D21) — superseded after F46.
- **EV-018**: AC-BB9 / TC-184 **PASS** (relevancy 0.778 / faith 0.938).
- **EV-029**: Wire `ce_scorer` in `from_settings`; promote spike to `infra/modal/rerank_app.py`;
  staging flag on; close #83 when staging smoke passes.
- **Inputs**: Retrieved top-N passages; CE model id; keep_k; packing (P1) fixed as F42.
- **Outputs**: Reranked top_k for synthesis when enabled; spike report + gate metrics; optional
  prod flag only after gate pass.
- **Protected surfaces**:
  | Surface | Change |
  |---------|--------|
  | Session spike scripts / Modal CE | Score pairs; measure relevancy/faith/cost |
  | `packages/rag` (if ship) | CE client + rerank merge |
  | `apps/chat-rag-backend` (if ship) | Flag-gated post-retrieve CE |
- **Out of scope unless gate passes**: Default-on CE; cheap R1 heuristic (already rejected on faith).
- **Ship gate**: Staging golden relevancy ≥ **0.28** and faith ≥ **0.91**; else spike-only.
- **Depends on**: **F46** (non-empty retrieve) before re-gate is valid.
- **Source**: S020 / EV-017; S021 / EV-018; GitHub #83/#161; S019 R3 spike; S020-D5/D7/D8/D21.

### F46: Staging retrieve reliability (non-empty pools)

- **What it does**: Restores **non-empty retrieve pools** on staging so golden eval and live
  ChatRAG asks return `sources` / passages again. S020 Path A observed `pool=0` / empty
  `sources` while F43 cache still worked — investigate embed↔corpus pin,
  `min_retrieval_score`, fixture URLs, and retrieve path bugs; ship the minimal fix
  (code, config, and/or corpus rebuild).
- **Inputs**: Staging corpus + embed pin; retrieve knobs (`top_k`, `min_retrieval_score`,
  language); golden fixture URLs; ChatRAG / F36 retrieve path.
- **Outputs**: Non-empty pools on staging golden rows and sample live asks; diagnostics for
  root cause; guard tests at the layer the emptiness was observed (API/e2e + optional staging).
- **Protected surfaces**:
  | Surface | Change |
  |---------|--------|
  | `packages/rag` / chat-rag retrieve | Bugfix or knob correction if code-side |
  | Corpus / embed pin / F41 rebuild | Ops remediations if pin drift |
  | tests / e2e | Non-empty retrieve assertions; bug repro if applicable |
- **Out of scope (EV-018)**: Multilingual embed swap (#159); synthesizer upsizing; LangGraph;
  changing F43/F44 defaults; closing #83 without F45 re-gate.
- **Success**: Staging golden + sample H3 asks show non-empty pools; unblocks F45 re-gate.
- **Source**: S021 / EV-018; S020 ce-ship-gate / evolve-summary follow-ups; S021-D8.

### F47: Skip re-ingest when content_hash unchanged (#163)

- **What it does**: When a URL’s scraped `content_hash` matches the stored document hash,
  skip chunk delete + re-embed (and re-chunk). Still **refresh document metadata**
  (title/language/timestamps/tags as applicable). Operators bypass with job `force=true`.
  Completes ingest-path skip that AC-RB4 / rebuild `force` anticipated but pipeline did not
  fully enforce on every re-ingest.
- **Inputs**: Scraped text → `content_hash`; existing document row hash; job `force`.
- **Outputs**: Job result/metrics (`skipped_unchanged` / equivalent); unchanged chunk vectors
  when skipped; metadata updated.
- **Protected surfaces**:
  | Surface | Change |
  |---------|--------|
  | Ingest pipeline / write API upsert | Hash compare short-circuit before delete-chunks |
  | Admin job options | `force` on ingest (align with rebuild) |
  | tests / e2e | Same-hash skip + force re-embed (UJ-062, TC-187–188) |
- **Out of scope (EV-019)**: Changing scrape normalization solely for hash stability beyond
  documented whitespace rules; ChatRAG retrieve path.
- **Success**: Unchanged corpus re-run skips embeds; forced re-run still rewrites chunks.
- **Source**: S022 / EV-019; GitHub #163; S022-D8 / S022-D14.

### F48: Embedding sub-batch + retry for ingest (#166)

- **What it does**: Makes ingest embedding calls resilient: split large chunk lists into
  sub-batches and retry transient Modal/HTTP failures with backoff. Contrasts with ADR-023
  tag fail-open — after exhausted retries, **fail the URL job** (no silent corpus holes).
  Dim mismatch / empty batch remain hard-fail without retry.
- **Inputs**: Chunk texts; embed client; Modal `/embed/batch` limits; retry knobs.
- **Outputs**: Successful embeddings under transient faults; clear job error when retries
  exhausted or hard-fail.
- **Protected surfaces**:
  | Surface | Change |
  |---------|--------|
  | `packages/embedding-client` | Sub-batch + retry |
  | Ingest pipeline | Uses resilient client; fail-URL on exhaust |
  | Modal embed app | Align batch limits if needed |
  | tests / e2e | Simulated 5xx/timeout recovery; hard-fail (TC-189–190) |
- **Out of scope (EV-019)**: Multi-provider embed ABC; changing tag fail-open.
- **Success**: Transient embed blips recovered; dim errors fail fast; exhaust → failed URL.
- **Source**: S022 / EV-019; GitHub #166; S022-D8 / S022-D12 / S022-D14.

### F49: Chunk overlap + HF tokenizer sizing (#160)

- **What it does**: Adds configurable **chunk overlap** (default **32** tokens) and sizes
  chunks with the HuggingFace tokenizer for pinned embed model `BAAI/bge-small-en-v1.5`
  (ADR-044). Deprecates word-count estimate. Existing corpus may need `rechunk` rebuild.
- **Inputs**: `chunk_size_tokens`, `chunk_overlap_tokens`; source text; tokenizer id.
- **Outputs**: Overlapping tokenizer-sized chunks; config + job option overrides; rebuild notes.
- **Protected surfaces**:
  | Surface | Change |
  |---------|--------|
  | `packages/ingest` chunker | Overlap + HF tokenizer |
  | config-spec / job options | `chunk_overlap_tokens` default 32 |
  | F41 rebuild / admin | `rechunk` when migrating live corpus |
  | dependency-inventory | transformers/tokenizers on ingest path |
- **Out of scope (EV-019)**: Context packing (#165); changing default `chunk_size_tokens` (256).
- **Success**: Overlap default 32; HF sizing; unit + e2e cover boundaries (TC-191–192).
- **Source**: S022 / EV-019; GitHub #160; S022-D6 / S022-D8 / S022-D15–D16; ADR-044.

### F59: Robust scrape — main-content, politeness, JS-render, PDF text (#69)

- **What it does**: Upgrades the ingest scrape layer beyond minimal HTMLParser extraction:
  main-content / boilerplate stripping; redirects, charset, content-type, timeouts/retries;
  robots.txt + rate limiting + descriptive User-Agent; **JS-rendered pages via Playwright in
  the Modal DM worker** (`VECINITA_SCRAPE_JS_RENDER=off|auto|always`, ADR-045); **basic PDF
  text extract** via `pypdf` (not full OCR); main-content via **`trafilatura`**. Richer
  `ScrapedDocument` metadata and structured per-fetch errors for jobs.
- **Inputs**: Public URL; scrape/politeness config; optional render path when HTML is sparse.
- **Outputs**: Cleaner title/body text; metadata (canonical URL, fetched-at, content-type,
  status); job-visible fetch errors.
- **Protected surfaces**:
  | Surface | Change |
  |---------|--------|
  | `packages/ingest` scrape/models | Extraction, politeness, PDF/JS paths |
  | DM pipeline / Modal worker | Consume upgraded scrape |
  | tests | HTML/PDF fixtures + failure modes |
- **Out of scope (EV-022)**: Full OCR product; auth-walled sites; multi-scraper provider ABC;
  ChatRAG UI.
- **Ship order**: First slice of epic #185 (before F60/F61).
- **Source**: S024 / EV-022; GitHub #69; S024-D7/D14/D16/D21/D22.

### F60: Website crawl from seed URL (#71)

- **What it does**: From a seed URL, discover and scrape same-site internal pages in one job
  with configurable depth/page limits, include/exclude patterns, URL normalize/dedup, link
  graph for tree rendering, and per-page soft failure. Additive `POST /jobs` options
  (`crawl`, `max_depth`, `max_pages`, scope) — not a separate `/jobs/crawl`. Admin Job form
  fields configure the crawl.
- **Inputs**: Seed in `urls[0]`; crawl options; shared politeness from F59.
- **Outputs**: Multiple documents + link-graph/parent metadata; partial success metrics;
  progress on Jobs detail.
- **Protected surfaces**:
  | Surface | Change |
  |---------|--------|
  | `packages/ingest` crawl module | BFS/scope/dedup/graph |
  | OpenAPI / job options | Additive crawl fields |
  | DM frontend JobForm | Crawl controls |
  | tests / e2e | Scope, depth, dedup, soft-fail |
- **Defaults (starting)**: `max_pages≈25`, `max_depth≈2`, polite delay (04 may refine).
- **Out of scope (EV-022)**: #94 curation; cross-domain crawl; auth crawl.
- **Ship order**: After F59; before F61.
- **Source**: S024 / EV-022; GitHub #71; S024-D8/D10/D11/D13/D22.

### F61: Corpus tree UI + nested source metadata (#70)

- **What it does**: Admin Corpus **tree view** (toggle with flat list) grouped
  **domain → URL path segments → document → chunks**, with expand/collapse, per-node status
  and counts, selection + bulk actions. Backend hierarchy payload for a job/corpus.
  **ChatRAG backend** may store/serve nested source metadata for future use — **no ChatRAG
  UI** this cycle (licensing research tracked separately).
- **Inputs**: Corpus/job hierarchy API; existing bulk dialogs.
- **Outputs**: Nested browse UX in DM; EN/ES labels; Vitest coverage of nesting behavior.
- **Protected surfaces**:
  | Surface | Change |
  |---------|--------|
  | `apps/data-management-frontend` | Tree component + CorpusPage toggle |
  | DM backend / write API | Hierarchy endpoints |
  | `apps/chat-rag-backend` | Nested source metadata only (no FE) |
  | tests | Vitest tree + API e2e as applicable |
- **Out of scope (EV-022)**: ChatRAG public tree UI; changing bulk action semantics beyond
  tree selection wiring.
- **Ship order**: After F60 (uses crawl graph / path metadata).
- **Source**: S024 / EV-022; GitHub #70; S024-D9/D12/D17/D18.

### F62: Husky lean pre-push + expanded pre-commit (#182)

- **What it does**: Restructures local Husky gates so **pre-push** runs **lint + unit tests
  only** and **pre-commit** runs the heavier local gates that previously bloated push
  (typecheck + security-scan) while keeping the BUG-2026-07-31 job_type dispatch guard.
- **Inputs**: Developer `git commit` / `git push`; env skip knobs.
- **Outputs**: Faster default pushes; documented tier table matching hooks.
- **Key parameters**:
  | Parameter | Default | Description |
  |-----------|---------|-------------|
  | `VECINITA_SKIP_PRE_PUSH` | unset | Skip pre-push entirely |
  | `VECINITA_SKIP_PRE_COMMIT` | unset | Skip pre-commit entirely |
  | `VECINITA_FULL_PRE_PUSH` / `VECINITA_MEDIUM_PRE_PUSH` | unset | Opt-in heavier push tiers |
  | `SEC_SKIP_SUPABASE_ADVISORS` | unset/auto | Token-gated advisors (unchanged) |
- **Protected surfaces**:
  | Surface | Change |
  |---------|--------|
  | `.husky/pre-push` → `scripts/ci/pre_push.sh` | Lint + `test-fast` only (default) |
  | `.husky/pre-commit` | Typecheck + security-scan + job-dispatch |
  | Makefile / docs / rules | Tier table + skip knobs |
- **Locks (S025-D5)**: format-check stays PR/`make ci-push` only; agent stop hooks **keep**
  typecheck (advisory); no lint-staged in this cycle.
- **Out of scope**: Replacing GitHub CI; full `ci-push` on every commit; #181 perf gate.
- **Source**: S025 / EV-023; GitHub #182 / #194.

### F63: Automate release tagging after main CD (#103)

- **What it does**: After successful production CD on `main`, create an immutable semver
  Git tag and GitHub Release so every deploy has a traceable marker.
- **Inputs**: Successful DigitalOcean deploy workflow (end of CI → preflight → Modal → DO chain).
- **Outputs**: Annotated tag `vX.Y.Z` + GitHub Release notes (SHA + CI/CD run URLs).
- **Key parameters**:
  | Parameter | Default | Description |
  |-----------|---------|-------------|
  | Bump policy | **patch** from last `v*` tag | Minimal automation (no semantic-release) |
  | Escape hatch | `[skip release]` in commit message | Skip tagging for docs-only / redeploy |
  | Idempotency | Skip if HEAD already tagged | No duplicate tags |
- **Locks (S025-D6)**: Trigger after **DO CD success**; annotated tag + GitHub Release; **no**
  floating `v1`/`v1.2` tags; **no** full conventional-commits semantic-release yet.
- **Out of scope**: CHANGELOG auto-rewrite beyond release notes body; tagging before Modal/DO.
- **Source**: S025 / EV-023; GitHub #103 / #194.

### F64: Cold-start wait — query tips + VECINA marketing (#87 residual)

- **What it does**: Extends F40 wait-surface catalog with typed entries (`fact` | `tip` |
  `marketing`) so cold-start / slow-stream UX also rotates **how-to-query tips** and
  **VECINA marketing** copy (EN/ES). No mini surveys. Reuses F40 consent + donate CTA.
- **Inputs**: Locale; wait UX active (cold-start retry or >8s no first token); consent prefs.
- **Outputs**: Richer rotating wait content; same cookie/localStorage posture as ADR-039.
- **Protected surfaces**:
  | Surface | Change |
  |---------|--------|
  | `apps/chat-rag-frontend` `coldstart/facts` | Typed catalog + rotation |
  | `packages/frontend-i18n` | Tip/marketing strings if not inlined in catalog |
- **Out of scope**: Mini surveys; CMS-backed content; Modal latency changes.
- **Source**: S026 / EV-024; GitHub #87 / #193; S026-D3/D14.

### F65: Ask energy estimate + use guide + advisory (#93)

- **What it does**: After each ask, ChatRAG backend returns a **heuristic** energy estimate
  (Wh + gCO₂e) derived from pinned prod GPU **T4 TDP 70 W × 50% util × ask wall time**,
  times a configurable US-average gCO₂e/kWh factor. FE shows estimate chip + permanent
  **estimate advisory** (approximate; not live Modal power metrics) and a primary
  **car-travel equivalent** line (“≈ X m / Y mi of average car travel”) from
  `g_co2e ÷ VECINITA_ENERGY_CAR_GCO2E_PER_KM` (default ~251 g/km ≈ EPA 404 g/mi).
  Use guide may also mention % of a typical car-day/year using optional day/year
  constants — still approximate. Includes a short bilingual **use guide** (better queries
  + env context), reusable on wait surface and/or chrome. Conceptual basis: Modal
  [GPU metrics](https://modal.com/docs/guide/gpu-metrics) power-as-proxy — **not** live
  dashboard telemetry per request.
- **Inputs**: Ask wall duration (backend); env constants for TDP/util/intensity/car.
- **Outputs**: `energy_estimate` on `/ask` and stream `done` (incl. car-distance fields);
  UI chip + car line + advisory; use guide.
- **Key parameters**:
  | Parameter | Default | Description |
  |-----------|---------|-------------|
  | `VECINITA_ENERGY_GPU_TDP_W` | `70` | T4 TDP watts |
  | `VECINITA_ENERGY_GPU_UTIL` | `0.5` | Assumed utilization |
  | `VECINITA_ENERGY_GCO2E_PER_KWH` | `386` | Grid intensity (US-avg-ish) |
  | `VECINITA_ENERGY_CAR_GCO2E_PER_KM` | `251` | Avg car gCO₂e/km (≈ EPA 404 g/mi) |
  | `VECINITA_ENERGY_CAR_GCO2E_PER_DAY` | optional | For use-guide % of car-day |
  | `VECINITA_ENERGY_CAR_GCO2E_PER_YEAR` | optional | For use-guide % of car-year |
- **Protected surfaces**:
  | Surface | Change |
  |---------|--------|
  | `apps/chat-rag-backend` | Duration + estimate helper; response field |
  | `apps/chat-rag-frontend` | Chip, car-distance line, advisory, use guide |
  | `docs/api-contract.md` / OpenAPI | `energy_estimate` schema |
- **Out of scope**: Live Modal power API; measured PUE; regional live grid APIs; live
  traffic/fleet data for car factors.
- **Source**: S026 / EV-024; GitHub #93 / #193; S026-D5/D12/D18; 02 M7 / S026-D22; ADR-047.

### F66: Action icon micro-interactions (#104)

- **What it does**: Shared action-bound icon animation pattern (`ActionIcon` or equivalent)
  in `packages/frontend-ui`: refresh=spin, send=pulse, destructive=shake/scale, etc.;
  honors `prefers-reduced-motion`. Apply across admin Health/Jobs/Corpus (+ optional press
  feedback) and ChatRAG Ask/send, clear/new chat, theme toggle.
- **Inputs**: Pending/loading flags on controls.
- **Outputs**: Consistent in-progress icon feedback; Vitest on class/`aria-busy`.
- **Protected surfaces**:
  | Surface | Change |
  |---------|--------|
  | `packages/frontend-ui` | Shared animation wrapper |
  | `apps/data-management-frontend` | Health/Jobs/Corpus (+ optional) |
  | `apps/chat-rag-frontend` | Ask/send + chrome actions |
- **Out of scope**: Lottie; route-level page transitions; new animation libraries.
- **Source**: S026 / EV-024; GitHub #104 / #193; S026-D15.

### F67: Bilingual tooltips / contextual hints (#106)

- **What it does**: Accessible shared **Tooltip** in `packages/frontend-ui` (Radix/shadcn-
  aligned); i18n keys `shared.tooltip.*` / `admin.tooltip.*` / `chat.tooltip.*`. MVP:
  theme + language toggles both apps + ≥1 domain control per app (e.g. Users force-sign-out,
  ChatRAG new chat / delete conversation). Supplements `aria-label`; keyboard focusable.
- **Inputs**: Locale; hover/focus on triggers.
- **Outputs**: Localized tooltips; Vitest EN/ES.
- **Protected surfaces**:
  | Surface | Change |
  |---------|--------|
  | `packages/frontend-ui` | Tooltip primitive |
  | `packages/frontend-i18n` | Typed tooltip keys |
  | Both frontends | MVP placements |
- **Out of scope**: Tooltips on dynamic API content (titles, tags, audit JSON); backend changes.
- **Source**: S026 / EV-024; GitHub #106 / #193; S026-D8/D15.

### F68: ChatRAG feedback page + backend (#186)

- **What it does**: ChatRAG **Feedback** control → `/feedback` page (category + required
  message; **no contact email**). `POST /api/v1/feedback` → internal-write → corpus
  `feedback` table (anonymous). Admin **Feedback** page (admin+super-admin) lists entries.
  Optional operator notify webhook/email on new row (not visitor identity). **90-day**
  retention + purge. ADR-046 amends ADR-004 for anonymous feedback rows only.
  **#214 follow-on (EV-214):** stronger bilingual no-PII/sensitive-data notice + UI callout;
  operator notify implemented on internal-write after successful insert — webhook
  (`VECINITA_FEEDBACK_NOTIFY_WEBHOOK`) and/or Resend email
  (`VECINITA_FEEDBACK_NOTIFY_EMAIL` + `RESEND_*`); fail-open (AC-UX18–19, TC-308–311).
- **Inputs**: Category enum; message text; locale chrome.
- **Outputs**: Stored feedback rows; admin list; privacy tests; optional operator webhook/email.
- **Protected surfaces**:
  | Surface | Change |
  |---------|--------|
  | `apps/database` | `feedback` migration + purge |
  | `apps/internal-write-api` | Write/list feedback; optional notify (#214) |
  | `apps/chat-rag-backend` / frontend | POST + page/button; notice polish (#214) |
  | `packages/frontend-i18n` | EN/ES privacy + intro copy (#214) |
  | `apps/data-management-frontend` / backend | Admin Feedback UI |
- **Out of scope**: Visitor email/PII; auto-attach chat transcripts; thumbs on messages;
  changing 90-day retention.
- **Source**: S026 / EV-024; GitHub #186 / #193 / **#214**; S026-D6/D13/D16/D17; ADR-046;
  EV-214-D1–D10.

### F69: Admin audit actor username (read-time) (#170)

- **What it does**: At admin audit **read** time, resolve `actor_id` → Supabase Auth
  **email** (fallback truncated UUID). Show on Audit Log / document history / user activity.
  **Never** persist email/name on `audit_log` rows (privacy AC-A6/U6/E8 unchanged).
  **Naming:** GitHub #170 / Fn title say “username”; product display and API field are
  **`actor_email`** (S026-D19 / 02 M1). Treat “username” as the issue alias, not a separate
  Supabase username field.
- **Inputs**: `actor_id` on audit rows; Supabase admin users lookup/cache.
- **Outputs**: Friendly actor label in admin UI; Vitest + optional API enrich field.
- **Protected surfaces**:
  | Surface | Change |
  |---------|--------|
  | `apps/data-management-backend` | Enrichment on audit list responses |
  | `apps/data-management-frontend` | Render `actor_email` / display label |
- **Out of scope**: Denormalizing names into corpus DB; ChatRAG identity; displaying a
  non-email Supabase “username” as the primary label.
- **Source**: S026 / EV-024; GitHub #170 / #193; S026-D7/D19; 02 M1.

### F70: Multilingual embedding runtime + model pin (#159)

- **What it does**: Replaces English-only prod pin `BAAI/bge-small-en-v1.5` with a
  **multilingual 384-d** model (prefer `intfloat/multilingual-e5-small` / E1 from S019).
  Updates Modal embedding app + shared `packages/embedding-client` so **ingest and query**
  share one pin. Prefer FastEmbed; **allow** sentence-transformers or custom ONNX on Modal
  when FastEmbed cannot host the winner (S027-D7). Applies e5 `query:` / `passage:` prefixes
  consistently when required. ADR-008 successor (dim stays 384 — no schema migration).
- **Inputs**: Model id / runtime choice; texts for `/embed` and `/embed/batch`; query vs
  passage mode.
- **Outputs**: 384-d vectors; health/model metadata; config pin
  (`VECINITA_EMBEDDING_MODEL_ID` and related); ADR-008 successor.
- **Protected surfaces**:
  | Surface | Change |
  |---------|--------|
  | `infra/modal/embedding_app.py` | Host winner model (FastEmbed and/or ST/ONNX) |
  | `packages/embedding-client` | Shared pin + prefix rules for ingest + ChatRAG |
  | ChatRAG + DM ingest paths | Consume shared client only |
  | `docs/adr` / config-spec | ADR-008 successor; pin defaults |
- **Out of scope**: Dual-index; dim≠384; UI; bge-m3 multi-vector.
  Tokenizer **aligns with embed pin this cycle** (S027-D15 amended by 02 M2b) via F71 rechunk.
- **Status**: Implemented (11-verify-impl S027-D47 2026-08-05; live cutover confirm @ 13).
- **Source**: S027 / EV-025; GitHub #159; S027-D1–D25; S019 spike E0/E1/E2.

### F71: Corpus re-embed + prod cutover (multilingual pin) (#159)

- **What it does**: Runs F41 rebuild with the F70 model pin on **staging first**
  (shadow → F36 EN/ES advisory report → operator promote), then **repeats on prod**
  (S027-D5/D21). Mode: **`rechunk` then re-embed** (or equivalent rebuild that re-tokenizes
  with the pin’s HF tokenizer and re-embeds) so `VECINITA_CHUNK_TOKENIZER_ID` matches the
  embed pin (**S027-D15 amended — 02 M2b**). Version stamps `embedding_model_id`,
  chunk settings, and `rebuild_run_id`. Promote is **operator judgment** after the report
  (S027-D11) — no hard numeric abort. Keep prior **E0 revision restorable** via F41 rollback
  (S027-D22). Optionally tune F44 soft language filter **only if** post-pin F36 shows
  ES/lang-filter harm (S027-D19/D20; no separate Fn).
- **Inputs**: F70 pin live on Modal; F41 rebuild (`mode=rechunk` and/or `reembed` as needed
  for tokenizer+embed); golden/eval set; promote path; optional F44 flag/thresholds.
- **Outputs**: Staging then prod re-chunked + re-embedded corpus; F36/dense metrics report;
  promote audit; rollback runbook; #159 closable or follow-on clearly ticketed.
- **Protected surfaces**:
  | Surface | Change |
  |---------|--------|
  | F41 rebuild / promote | Stamp + run with F70 model id + aligned tokenizer; staging then prod |
  | Admin Jobs UI | Operator enqueue/promote (existing) |
  | ChatRAG retrieve | Reads new vectors after promote |
  | F36 / eval harness | EN vs ES evidence for ship call |
  | `packages/rag` (optional) | F44 threshold/flag tune if harm shown |
  | config / ADR-044 | `VECINITA_CHUNK_TOKENIZER_ID` set to embed pin |
- **Out of scope**: Dual-write dim migration; rescrape-as-default; UI redesign of Jobs;
  standalone F72.
- **Status**: Implemented (11-verify-impl S027-D47 2026-08-05; live staging→prod cutover confirm @ 13).
- **Source**: S027 / EV-025; GitHub #159; F41 / ADR-040; S027-D1–D25; 02 M2b.

### F72: Citation UI — validate URLs before href (#222)

- **What it does**: In ChatRAG `SourceList` (and sibling citation UI), only render a clickable
  `<a href>` when `source.url` is a valid absolute **`http:` / `https:`** URL. Invalid,
  relative, `fixture://`, `javascript:`, or empty values show **title / label as plain text**
  (no href). **Display filter only** — ingest, scrape, and job acceptance are unchanged;
  backend may still store fixture/malformed URLs for tests (S028-D6).
- **Inputs**: `sources[].url` / `sources[].title` from ask/stream.
- **Outputs**: Link only when validator passes; otherwise plain-text title.
- **Protected surfaces**:
  | Surface | Change |
  |---------|--------|
  | `packages/frontend-ui` (`vecinita-frontend-ui`) | Shared `isSafeHttpUrl` / citation href helper + Vitest |
  | `apps/chat-rag-frontend` | `SourceList` consumes helper (Vitest) |
- **Out of scope**: Ingest/job URL rejection; corpus cleanup; admin ingest forms this cycle (helper reusable later).
- **Status**: Implemented (S028/EV-026; 11-verify-impl S028-D32).
- **Source**: S028 / EV-026; GitHub #222; RD-310 / RD-317 / RD-323.

### F73: Dynamic relevance-gated sources (no fixed pad) (#223)

- **What it does**: Treat `top_k` as an **upper bound**, not a display quota. After retrieve
  (and CE/rerank when enabled), **omit** hits below `min_retrieval_score` (dense score when
  CE off — S028-D9 / OQ6). Do **not** pad `sources[]` to a fixed count. Synthesis context and
  UI citations use the **same** filtered set. Length is **0…top_k**. Empty/few sources remain
  valid when nothing clears the bar. Follow-on to F50 (adaptive / retrieve-N-show-K was OOS
  in EV-020).
- **Inputs**: Existing retrieve knobs (`VECINITA_TOP_K`, `min_retrieval_score`; CE flags if on).
- **Outputs**: `sources[]` length 0…top_k by relevance; no FE pad.
- **Protected surfaces**:
  | Surface | Change |
  |---------|--------|
  | `packages/rag` | Filter helper / retrieve post-process |
  | `apps/chat-rag-backend` | Ask/stream `sources[]` assembly |
  | config-spec / api-contract | Document max vs quota semantics |
- **Out of scope**: Corpus curation (#94/#217); groundedness (#84) except citation-filter overlap; changing default `top_k=8` as a *target*.
- **Status**: Implemented (S028/EV-026; 11-verify-impl S028-D32).
- **Source**: S028 / EV-026; GitHub #223; F50; RD-311.

### F74: Operator-settable `display_title` (#224)

- **What it does**: Adds nullable **`documents.display_title`**. Scrape/re-ingest always
  updates raw **`title`**. Operators set/override **display name** via DocumentAdmin
  single-doc rename and F27 bulk metadata. Citations, packing headers, and admin lists use
  **`COALESCE(display_title, title)`**. Clearing `display_title` (null) resets to scraped
  `title`. Chunk-facing titles **inherit** the document display name. Ingest/job
  `title` → `display_title` **deferred** (RD-321 / S028-D22 TP2). Audit: `document.edited`
  with before/after including `display_title` (S028-D10/D11).
- **Inputs**: Operator PATCH / bulk metadata; scrape title.
- **Outputs**: Durable human display name; ChatRAG `sources[].title` = display string
  (compatible field name — S028-D12).
- **Protected surfaces**:
  | Surface | Change |
  |---------|--------|
  | `apps/database` | Alembic: `documents.display_title` |
  | internal-write-api | `PATCH /internal/v1/documents/{id}`; bulk metadata accepts `display_title` |
  | data-management-frontend | DocumentAdmin single-doc rename |
  | `packages/rag` / ChatRAG | Packing + `sources[].title` from display coalesce |
- **Out of scope**: LLM title generation; community end-user edit; #94/#217 source-add curation.
- **API/version**: Prefer compatible nullable column; if breaking unavoidable → major bump (S028-D15).
- **Status**: Implemented (S028/EV-026 M125).
- **Source**: S028 / EV-026; GitHub #224; F27; RD-312–RD-315.

### F75: Optional ingest bilingual translation (#251)

- **What it does**: Opt-in **`translate_locales`** on ingest/crawl jobs (default off). After
  chunking, the pipeline calls **`vecinita-llm`** per-chunk MT and upserts a **locale sibling**
  document linked via **`paired_document_id`**. Translations default to **`publish_status=draft`**
  until an operator promotes via **`PATCH /internal/v1/documents/{id}`**. ChatRAG pgvector retrieval
  excludes drafts. URL uniqueness becomes **`(url, language)`** so EN and ES siblings share the
  scrape URL.
- **Inputs**: Ingest job `options.translate_locales` (e.g. `["es"]`); operator promote PATCH.
- **Outputs**: Draft paired document + job metrics (`translated_documents`, `translated_chunks`).
- **Protected surfaces**:
  | Surface | Change |
  |---------|--------|
  | `apps/database` | Alembic: `paired_document_id`, `publish_status`, `uq_documents_url_language` |
  | data-management-backend | Post-chunk translate branch + metrics |
  | internal-write-api | Batch upsert returns document IDs; PATCH `publish_status` |
  | `packages/rag` | Retriever filters `publish_status = 'published'` |
  | data-management-frontend | JobForm “Also create Spanish translation” checkbox |
- **Out of scope**: auto-translate on all ingests; live prod corpus mutation without operator
  approval. (#245 dashboard parity → **F76**.)
- **Status**: Implemented (EV-030).
- **Source**: EV-030; GitHub #251; ADR-052.

### F76: Corpus language parity metrics + badges (#245)

- **What it does**: Extends admin **dashboard** and **corpus list** so operators see **document and
  chunk counts by language**, **published parity gap totals** (EN-only / ES-only via
  `paired_document_id`), and **Missing Spanish / Missing English** badges on unpaired rows. Includes
  a **staging bulk-translate** script that queues F75 `translate_locales: ["es"]` jobs for EN-only
  published documents.
- **Inputs**: `GET /internal/v1/stats/summary`; paginated `GET /internal/v1/documents` (existing
  `paired_document_id` / `publish_status` fields).
- **Outputs**: Aggregate parity metrics (no PII); per-row parity badges; bulk job report artifact.
- **Protected surfaces**:
  | Surface | Change |
  |---------|--------|
  | `packages/shared-schemas` | `StatsSummaryResponse.chunk_language_breakdown`, `parity_gaps` |
  | internal-write-api | Stats SQL for chunk language + parity counts |
  | data-management-frontend | Dashboard language table; `ParityBadge` on corpus list + detail |
  | Session scripts | `staging-bulk-translate-en-to-es.sh` (staging only) |
- **Out of scope**: ChatRAG browse parity chips; `es_esl_supplement` retirement; live prod bulk
  translate without AskQuestion; URL-heuristic pairing.
- **Status**: Implemented (EV-031).
- **Source**: EV-031; GitHub #245; ADR-052.

### F78: Corpus change automations (#73)

- **What it does**: When corpus content is added or changed, enqueue **catch-up** work
  (failed/partial jobs, missing embeddings; optional retag) — **not** re-embed when
  already complete (RD-334). Triggers: job completion, cron catch-up, and document
  CRUD hooks that enqueue async Modal jobs (`document_id`+`revision` idempotent key). Shares
  **one** Modal schedule with F79 (two job types). Kill-switch + cost/concurrency caps;
  run history in Postgres via write-API; DM UI enable/disable + history (ADR-052).
- **Inputs**: Job completion events; cron ticks; document CRUD; config flags/caps.
- **Outputs**: Automation jobs; `automation_runs` history (status, last run, errors).
- **Protected surfaces**: `infra/modal/data_management_app.py`; DM backend/FE; write-API
  + schema for run history.
- **Journeys / tests**: UJ-082; TC-266–269, TC-270; AC-AU1–AU6.
- **Out of scope**: #192 dashboard widgets; fine-tune train (→ F80); source refresh (→ F79);
  auto F41 on every change.
- **Status**: Live enabled (EV-031 M133/M135). Run history via `POST /automations/runs` + worker persist (PR #266).
- **Source**: S030 / EV-027; GitHub #73; S030-D2–D8, D16–D19, D23, D64; ADR-052; S031; EV-031.

### F79: Corpus freshness automation (#219)

- **What it does**: Keep registered URL sources current via scheduled or triggered
  re-fetch/re-crawl; stale detection (default **30 days**); change-aware ingest
  (`content_hash` skip + last_checked bump); operator enable/disable per source and
  “Refresh now”. Shares Modal schedule with F78 (ADR-052).
- **Inputs**: Registered source URLs; schedule config; operator refresh actions.
- **Outputs**: Refreshed or verified documents; stale/last_checked visible in Admin.
- **Protected surfaces**: Modal schedule (shared with F78); packages/ingest; DM FE;
  write API / schema as needed.
- **Journeys / tests**: UJ-083; TC-271–274, TC-270; AC-FR1–FR6.
- **Out of scope**: Fine-tune (#72/F80); guaranteeing third-party uptime.
- **Status**: Live enabled (EV-031 M133). TC-291 PASS — stale/`last_checked_at` visible on live admin list.
- **Source**: S030 / EV-027; GitHub #219; S030-D7, D18–D19, D64; ADR-052; S031; EV-031.

### F80: Modal LoRA fine-tune + human promote (#72)

- **What it does**: Fine-tune the chat LLM on the RAG corpus via Modal using **LoRA/PEFT**
  on the pinned Qwen model. Training data: **instruction/QA SFT pairs** from chunks.
  Version adapters on a Modal Volume. Each train requires **manual approve**. Eval
  report (base vs adapter) is shown to the operator; **promote is human judgment only**
  (no automated metric abort) — operator should promote only when they judge better than
  base. Prod `vecinita-llm` loads adapter **only after promote**; playground optional
  for pre-promote (ADR-053). With GPU memory snapshots (ADR-022), adapters are resolved
  **after restore** and verified with **SHA-256** (`VECINITA_FINETUNE_ADAPTER_HASH`,
  AC-FT11 / #316) — not baked into the snapshot.
- **Inputs**: Corpus-derived SFT set; operator approve; eval golden/held-out set.
- **Outputs**: Versioned LoRA adapter; eval report; optional promoted serve.
- **Protected surfaces**: new `infra/modal/` FT module; `llm_app.py`; llm-client; eval
  harness; admin FE approve/promote UX.
- **Journeys / tests**: UJ-084; TC-275–279; AC-FT1–FT9.
  (“Eval-gated” = human promote after eval evidence — RD-338; not automated abort.)
- **Out of scope**: Full-weight FT default; auto-load latest on prod; blind promote
  without operator review.
- **Status**: Eval path live (EV-031 M134) — `VECINITA_FINETUNE_ENABLED=true`, `vecinita-llm-finetune`
  deployed; prod adapter pin empty (`adapter_id: null`). **Prod promote deferred** — human
  judgment + AskQuestion for live cutover (ADR-053).
- **Source**: S030 / EV-027; GitHub #72; ADR-009, ADR-037, ADR-053; S030-D5, D10–D12,
  D20–D22, D64; S031.

### F81: LLM query refinement before retrieval (#82)

- **What it does**: Optional **LLM rewrite** step before pgvector retrieve — transforms the
  raw user question into 1–`REFINE_COUNT` alternate retrieval queries via **`vecinita-llm`**
  (self-hosted). Distinct from **F42 H7** heuristic fan-out (rules/locale variants). Refinement
  preserves user **locale** (no cross-language translation). Merged retrieve dedupes by chunk id
  (same merge as H7). Flag-gated default **off** until F36 / `rag-regression` evidence on staging.
- **Inputs**: Raw question; detected locale; tag vocabulary context (read-only).
- **Outputs**: Refined query list fed to retrieve; fallback to raw question on LLM/parse failure.
- **Protected surfaces**:
  | Surface | Change |
  |---------|--------|
  | `packages/rag` | `refine_query_llm` + merge hook before retrieve |
  | `apps/chat-rag-backend` | Flag-gated call in ask path (before `_retrieve`) |
  | `packages/llm-client` | Shared chat-template prompt for rewrite JSON |
- **Interaction**: Runs **before** F22 tag-filtered retrieve; composes with F42 H7 and F45 CE
  (refine → multi-query → retrieve-N → CE → pack).
- **Out of scope**: LangGraph orchestration; paid rewrite APIs; translating user language away.
- **Ship gate**: Staging F36 + `rag-regression` must not regress beyond EV-028 tolerances; if no
  lift, ship wiring with flag default-off and keep #82 open for follow-up.
- **Source**: EV-029; GitHub #82; #76 umbrella; ADR-009 / ADR-037.

### F82: Output verification + inline citations (#84)

- **What it does**: Optional **post-generation groundedness check** before the user sees an
  answer: score faithfulness with the same self-hosted LLM YES/NO judge used by F36 eval
  (`score_faithfulness`). When the verdict is below threshold, **prepend** a bilingual hedge
  disclaimer (intake S034-D2). When enabled, append inline **`[1]`…`[N]`** citation markers
  mapped to `sources[]` order. Runs on both `/ask` and `/ask/stream` by buffering the full
  generation, verifying, then emitting (S034-D3).
- **Inputs**: Question, packed retrieval context, draft LLM answer, locale, ranked sources.
- **Outputs**: Final answer string (hedge + body + citations); unchanged `sources[]` shape.
- **Protected surfaces**:
  | Surface | Change |
  |---------|--------|
  | `packages/rag` | `verify_and_format_answer`, hedge + citation helpers |
  | `apps/chat-rag-backend` | Flag-gated hook after `_synthesize` / stream buffer |
  | `packages/eval` | `OutputVerificationScorer` adapter (ADR-033 §9) |
- **Interaction**: Runs **after** F45 CE retrieve and F81 refine paths; before F43 cache store.
- **Out of scope**: NLI entailment Modal app; regenerate-on-fail; prod flag without AskQuestion.
- **Ship gate**: Wiring ships with flag default-off; **live `VECINITA_RAG_OUTPUT_VERIFY=true`**
  after F36 / `rag-regression` non-regression + operator approval (S034-D10 / AC-OV7).
- **Source**: EV-030; GitHub #84; ADR-033 §9; ADR-009 / ADR-037.

### F83: Distinct staging environment (DO + Supabase + Modal)

- **What it does**: Provisions a **true non-prod staging** stack that mirrors production:
  DigitalOcean apps + Managed Postgres, Supabase Auth project, and Modal Apps in the same
  workspace **`vecinita`** under Modal Environment **`staging`** (web suffix `staging`;
  native Environments). Restores staging→prod paths and ends operational use of
  `staging_as_live` (ADR-049) once staging is healthy. Requires GitHub ruleset so merges to
  `main` need CI **and** staging deploy + H1–H5 smoke.
- **Inputs**: Operator tokens (DO, Modal workspace `vecinita`, Supabase); GitHub Environments
  `staging` / `production`; seed corpus for staging DB only.
- **Outputs**: Distinct staging URLs; `env_role: staging` \| `prod`; ADR-054; updated
  runbook/secrets/CD; always-applied Stage→Main agent rule (EV-033); GH tracking via #212.
- **Acceptance**: AC-ST1–AC-ST8; TC-294–TC-298; UJ-087.
- **Out of scope**: Live corpus clone without AskQuestion; Modal provision during Spec band
  (Build gate); full hostname rename of legacy prod apps in one cutover.
- **Promotion (EV-036-D15)**: When `origin/stage` exists — feature→`stage` (CI) then
  promote `stage`→`main` (CI + `staging-smoke`). Smoke remains on main-bound PRs (ADR-054).
- **Source**: EV-staging-do-supabase; EV-033-stage-before-main; EV-036-D15; ADR-054;
  ADR-049 exit; ADR-050.

### F84: Admin monitoring + staging Grafana/Loki/alerts (#114)

- **What it does**: Gives operators a dedicated Data Management **Monitoring** tab with
  privacy-safe success/failure rates and trends for **ingest** (jobs), **chat** (outcome
  metadata only), and **embed** (pipeline-stage / Modal invoke metrics). Complements F25
  corpus analytics, F26 point-in-time health, and F32 per-job lists. Also deploys a
  **staging-only** micro Grafana + Loki + Alertmanager stack (`infra/observability/` on a
  small Droplet) for Modal/DO SLO panels, short-retention logs (ADR-004 allow-list), and
  webhook alerts. **Prod always-on Grafana is deferred** until an explicit cost AskQuestion
  (ADR-004 ≤$50 hard cap).
- **Inputs**: Existing `jobs` rows; ChatRAG fire-and-forget operational events
  `{ outcome, latency_ms, error_code?, locale? }` (never `question`/`answer`); embed stage
  events correlated to ingest `job_id`; admin Supabase JWT; staging obs secrets
  (`VECINITA_ALERTMANAGER_WEBHOOK_URL`, etc.).
- **Outputs**: Allow-listed Postgres metrics tables + hourly rollups; admin APIs
  `GET /internal/v1/metrics/summary` and `…/timeseries`; `/monitoring` UI (en/es); staging
  Grafana dashboards + Loki + ≥1 Alertmanager rule to a generic webhook.
- **Acceptance**: AC-MON1–AC-MON8; UJ-088–UJ-089; TC-299–TC-306; ADR-055.
- **Out of scope**: Chat transcripts/replay; PostHog/Segment identity analytics; per-end-user
  analytics; PagerDuty; prod Grafana this cycle; full OpenTelemetry APM (P5 remains deferred).
- **Source**: EV-036-admin-monitoring-grafana; GitHub #114; ADR-004; ADR-055; F17/F25/F26/F32.

## Planned / Deferred (post-v1)

| # | Feature | Priority | Complexity | Notes |
|---|---------|----------|------------|-------|
| P1 | Dedicated API gateway / BFF | Medium | Medium | R6 unresolved — direct backend URLs in v1 |
| P2 | Multimodal / full OCR ingest | Low | High | **F59** covers basic PDF text; full OCR still deferred |
| P3 | Model fine-tuning on corpus | Low | High | **Superseded in-cycle by F80** (S030/EV-027 #72); was “excluded from v1” |
| P4 | Advanced admin (bulk reindex, A/B prompts) | Low | Medium | — |
| P5 | Full APM / OpenTelemetry | Low | Medium | Basic logs in v1 (F17); **F84** adds product metrics + staging Grafana/Loki only — not full APM |
| P6 | ChatRAG nested corpus UI | Medium | Medium | Deferred — licensing research (S024-D17) |

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
