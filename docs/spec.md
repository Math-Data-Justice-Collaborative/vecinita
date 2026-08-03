# Technical Specification

> **Project**: Vecinita  
> **Repository**: `/root/GitHub/VECINA/vecinita`  
> **Version**: greenfield (`fresh-start` branch)  
> **Last updated**: 2026-07-30 (EV-015 F41 corpus document store + rebuild)

## Overview

Vecinita is a **five-application monorepo** delivering a **bilingual (English/Spanish) community Q&A RAG chatbot** (ChatRAG) and a **data management platform** (scrape, chunk, embed, corpus admin). Deployment is **hybrid**: DigitalOcean hosts HTTP APIs that touch Postgres, both React frontends, and managed Postgres; **Modal** hosts async ingest workers, FastEmbed, **vLLM** (primary LLM per ADR-009), and the **Data Management ASGI API** (`requires_proxy_auth`). RAG orchestration uses **LlamaIndex** in `packages/rag`. The system enforces **zero personal data**, **US-only** infrastructure, and a **≤ $50/month** cost cap (target $25) per ADR-004.

## System Architecture

Five deployable applications share Postgres (pgvector) and internal packages. **Only DigitalOcean backends hold `DATABASE_URL`**; Modal workers persist data by calling a **DO internal write API** (RD-016).

**Diagrams:** Mermaid deployment topology, ERD, sequences, state machines, and class diagrams live in [data-flow.md](data-flow.md) and [architecture.md](architecture.md). User journey maps: [user-journeys.md](user-journeys.md#visual-journey-maps).

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         DigitalOcean (US: nyc1/sfo3)                          │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────────────┐  │
│  │ chat-rag-frontend│  │data-mgmt-frontend│  │ DO Managed Postgres       │  │
│  │   (React/Vite)   │  │   (React/Vite)   │  │ + pgvector (384-dim)      │  │
│  └────────┬─────────┘  └────────┬─────────┘  └────────────▲─────────────┘  │
│           │                     │                          │                 │
│           v                     v                          │                 │
│  ┌──────────────────┐  ┌──────────────────┐               │                 │
│  │ chat-rag-backend │  │ (optional) DO     │───────────────┘                 │
│  │ FastAPI +        │  │ internal write API│  DATABASE_URL only on DO       │
│  │ packages/rag     │  │ for Modal workers │                               │
│  └────────┬─────────┘  └────────▲─────────┘                               │
└───────────┼─────────────────────┼───────────────────────────────────────────┘
            │                     │
            │ HTTP                │ HTTP (service secret)
            v                     │
┌───────────┴─────────────────────┴───────────────────────────────────────────┐
│                              Modal (US workspace)                             │
│  ┌─────────────────────┐  ┌──────────────┐  ┌────────────────────────────┐ │
│  │ data-mgmt ASGI      │  │ scrape/ingest│  │ FastEmbed + vLLM (primary) │ │
│  │ /jobs/*  proxy auth │→ │ queue workers│→ │ Ollama fallback if needed   │ │
│  └─────────────────────┘  └──────────────┘  └────────────────────────────┘ │
└───────────────────────────────────────────────────────────────────────────────┘
```

### Component Overview

| Component | Purpose | Location | Dependencies |
|-----------|---------|----------|--------------|
| ChatRAG Backend | `/api/v1/ask`, streaming; LlamaIndex RAG; pgvector read | `apps/chat-rag-backend` | `packages/rag`, DO Postgres, Modal embed+LLM |
| ChatRAG Frontend | Bilingual chat UI, streaming display | `apps/chat-rag-frontend` | ChatRAG Backend API |
| Data Management ASGI | Job API, operator-facing HTTP (Modal proxy auth) | `apps/data-management-backend` (Modal) | Modal queues, DO internal write API |
| Ingest workers | Scrape → chunk → embed → call DO write API | Modal (`apps/data-management-backend`) | FastEmbed, DO internal API |
| Data Management Frontend | Jobs + corpus admin UI; **bilingual UI chrome** (EV-004 F31) | `apps/data-management-frontend` | Modal ASGI, internal-write API, `packages/frontend-*` |
| Database app | Alembic, pgvector, seeds, privacy tests | `apps/database` | Postgres |
| Internal write API | Upsert documents/chunks/embeddings; corpus CRUD | DO App Platform (**standalone** service) | Postgres only |
| Shared RAG | LlamaIndex pipelines; **P3 packer + H7** (F42/F51); **top_k=8** (F50); **H1 cache** (F43); optional **L1 soft language** (F44); gated **CE rerank** (F45); **retrieve reliability** (F46) | `packages/rag` | LlamaIndex, pgvector client |
| Shared ingest | Scrape/chunk helpers | `packages/ingest` | — |
| Embedding client | HTTP client to Modal FastEmbed | `packages/embedding-client` | Modal |
| Shared tagging | LLM/human tag prompts, vocabulary merge, cap enforcement | `packages/tagging` | Modal LLM (vLLM), config-spec |
| **Frontend i18n** | Locale detection, storage, EN/ES message tables (`t()`) | `packages/frontend-i18n` | None (pure TS) — EV-004 F31 |
| **Frontend UI** | Shared React locale provider, language toggle, tag/pagination primitives | `packages/frontend-ui` | `frontend-i18n`, Tailwind, minimal shadcn — EV-004 F31 |

**Package rule (RD-014):** `packages/*` must not import `apps/*`; apps depend on packages only.

## Component Details

### ChatRAG Backend

- **Purpose**: Stateless bilingual Q&A with retrieval and streaming generation; **public corpus read** (EV-001); **H7+P1 packing** (EV-016 F42); **H1 answer/retrieval cache** (EV-017 F43); optional **soft language fallback** (F44); gated **CE rerank** (F45); **staging retrieve reliability** (EV-018 F46).
- **Inputs**: `POST /api/v1/ask`, `POST /api/v1/ask/stream` (JSON: question; optional `tags[]`); **GET** `/api/v1/documents`, `/api/v1/tags`, `/api/v1/documents/{id}` (public browse).
- **Outputs**: Answer JSON or SSE token stream; source chunk references (IDs, not PII); optional `cache_hit` metadata (F43).
- **Algorithm**:
  1. Auto-detect query language (en/es).
  2. **F43 H1 cascade (default on):** exact answer cache (normalized query+locale content-hash) → semantic answer cache (conservative cosine; miss → continue) → retrieve-result cache → else generate path below; store on miss. Keys never identity-keyed (ADR-004). TTL + size cap; bust on corpus version / F41 rebuild.
  3. Embed query via Modal FastEmbed (HTTP) — prod pin **E0** `BAAI/bge-small-en-v1.5` (384-d).
  4. pgvector similarity search on DO Postgres; **optional tag filter** (user-selected or LLM-inferred).
     **F46 (EV-018):** staging must return non-empty pools for in-corpus questions — diagnose
     embed↔corpus pin, `min_retrieval_score`, golden fixture URLs, or retrieve bugs; fix before
     treating CE ship metrics as valid (EV-017 empty-pool lesson).
  5. **F44 L1 (default off):** if same-lang retrieve is empty above `min_retrieval_score`, optionally retry without language filter.
  6. **H7 (default on, F42):** thin multi-query fan-out — 2–3 **cheap heuristic** rewrites
     (locale-aware string variants, **not** LLM rewrites; Spanish-aware for `es`), retrieve per
     rewrite, merge/dedupe by chunk id / score, keep `top_k`.
  7. **F45 CE (default off):** if enabled after ship gate, rerank top-N with `BAAI/bge-reranker-v2-m3`, keep `top_k`.
     **Re-gate (EV-018):** run AC-BB9 / UJ-060 only after F46 non-empty pools (AC-FO1).
  8. **P3 pack (F42 + F51):** format each chunk as `Source: {title}\nURL: {url}\n{text}` via
     `packages/rag` helpers, then **document_id dedupe + char budget** (prod default; was P1-only
     in EV-016). `p1` remains available via `VECINITA_RAG_PACKER=p1`.
  9. Synthesize with packed context; stream or return completion via Modal LLM HTTP; populate cascade stores on generate.
- **Key parameters**: See `docs/config-spec.md`: `top_k` (default **8**, F50), H7/P3, cache, soft language, CE flags.
  F46 may adjust retrieve knobs or corpus pin ops without new product env vars unless 04 unlocks.
- **Error handling**: 4xx for validation (including rejected identity fields); 5xx with request ID in logs (no raw prompt persistence).
- **Latency**: Target **p95 < 15s** excluding cold start (RD-017); cache hits should be ≪ generate path.
- **Source**: feature-list F1–F6, F42–F46; S019/EV-016; S020/EV-017; S021/EV-018

### ChatRAG Frontend

- **Purpose**: Public chat UI; client-side conversation state only; **corpus browse** and **tag filter sidebar** (EV-001); **bilingual UI chrome** via shared packages (EV-004 F31); **cold-start / long-wait UX** with rotating fun facts + consent (EV-014 F40).
- **Inputs**: User messages in browser; tag chip selection for RAG; browse filters (tags, title/URL search); locale from `vecinita.locale` / browser detect; optional cold-start consent cookie + seen-fact ids (device-local only).
- **Outputs**: Rendered answers; calls streaming endpoint; browse list opens **original document URL** in new tab (no in-app reader); UI strings from `packages/frontend-i18n` (+ ChatRAG message tables); wait-status region with facts / donate CTA / consent banner during cold start or >8s first-token delay.
- **Cold-start wait (F40)**: Reuse `streamAsk` retry + `prewarmChatServices`; rotate ~10 static EN/ES facts; no API/CMS; no Modal changes.
- **Source**: feature-list F11, F19, F22, F31, F40

### Data Management (Modal ASGI + workers)

- **Purpose**: Operator-triggered ingest / retag / eval / **rebuild** jobs and job status.
- **Inputs**: `POST /jobs` (URLs, options including `job_type` + rebuild `mode`); `GET /jobs/{id}`;
  Jobs SSE; protected by Modal `requires_proxy_auth` + deploy secret at edge.
- **Outputs**: Job records (URL, status, error codes — no operator identity); rebuild progress.
- **Algorithm** (ingest):
  1. ASGI enqueues scrape job on Modal queue.
  2. Worker fetches URL(s): **F59** main-content via **`trafilatura`**, redirects/charset/content-type,
     robots.txt + rate limit + descriptive UA; **JS-render via Playwright in Modal DM worker**
     when `VECINITA_SCRAPE_JS_RENDER` is `auto`/`always` (ADR-045); **PDF** via **`pypdf`**
     best-effort — soft-fail page if no extractable text (S024-D29). Richer scrape metadata
     on the document.
  3. **Optional crawl (F60):** when `options.crawl=true`, seed = `urls[0]`; BFS same-site
     (domain / path-prefix scope), `max_depth` / `max_pages`, URL normalize/dedup, link graph;
     **per-page soft fail** — continue crawl; record page errors in job metrics (S024-D13).
  4. **Persist normalized body** to Postgres document store via internal-write (F41 / ADR-040),
     including **path/parent nested source fields** for tree + ChatRAG backend meta (F61).
  5. **Content-hash skip (F47 / #163):** if `content_hash` matches stored document and
     `force` is false → refresh metadata (title/language/timestamps; tags if retagged) but
     **skip** re-chunk, delete-chunks, and re-embed; record skip in job metrics. If `force`
     or hash differs → continue.
  6. **Chunk** text with HF tokenizer for embed pin + `chunk_overlap_tokens` (F49 / ADR-044).
  7. **LLM auto-tag** document (and optional chunk tags) from seeded vocabulary + allow new tags (F20)
     — fail-open per ADR-023.
  8. Call FastEmbed on Modal via **sub-batched embed client with retries** (F48 / #166). On
     exhausted retries or dim mismatch → **fail that URL** (not silent partial corpus).
  9. **POST chunks/embeddings/tags to DO internal write API** (not direct Postgres).
  10. Update job status via job store on Modal.
- **Corpus tree (F61):** Admin Corpus toggles **tree vs flat**; hierarchy
  domain → URL path segments → document → chunks via nested JSON APIs; selection + bulk
  actions. ChatRAG **backend** may expose nested source metadata — **no ChatRAG UI** this
  cycle (licensing research).
- **Algorithm** (rebuild — F41):
  1. Operator enqueues `job_type=rebuild` with `mode` (`reembed`|`rechunk`|`rescrape`), optional
     `document_ids`, `force`, `dry_run` (Admin Jobs UI).
  2. Worker reads body from **document store** (store-backed modes); `rescrape` may refresh store from URL.
     Existing corpus gets **one-time backfill** into store (02 M4).
  3. Re-chunk and/or re-embed per mode; stamp revision / `rebuild_run_id`.
  4. If `dry_run`, write **shadow** rows; run **F36 against shadow before promote**; operator
     promotes via **Admin UI** → internal-write promote (02 M2/M3).
  5. Retag is **not** part of rebuild (separate job).
- **Source**: feature-list F7–F10, F20, F32, F41, **F59–F61**; RD-016; ADR-040; S024/EV-022

### DO internal write API

- **Purpose**: Sole component(s) with `DATABASE_URL`; accepts service-authenticated writes from Modal; serves stats, audit, bulk operations, health aggregation (EV-002), and **rebuild promote / store upserts** (EV-015).
- **Inputs**: Authenticated requests (mTLS, API key, or private network) with document/chunk/embedding/tag payloads (**incl. `body_text`**); chunk list; tag PATCH; bulk operations (F27); stats increment (F28); audit queries (F29); rebuild promote.
- **Outputs**: Upserted rows; corpus list/delete; chunk list; tag CRUD for admin (F21); aggregated stats (F25); audit log entries (F29); serving stats (F28); promoted rebuild revisions.
- **New endpoints (EV-002)**:
  | Method | Path | Feature |
  |--------|------|---------|
  | GET | `/internal/v1/stats/summary` | F25 — aggregated dashboard stats |
  | POST | `/internal/v1/stats/served` | F28 — increment serving counter |
  | GET | `/internal/v1/stats/top-served` | F28 — top served documents |
  | DELETE | `/internal/v1/documents/bulk` | F27 — bulk delete |
  | PATCH | `/internal/v1/documents/bulk/tags` | F27 — bulk tag |
  | POST | `/internal/v1/documents/bulk/retag` | F27 — bulk LLM re-tag |
  | PATCH | `/internal/v1/documents/bulk/metadata` | F27 — bulk edit metadata |
  | GET | `/internal/v1/audit` | F29 — global audit log (paginated, filterable) |
  | GET | `/internal/v1/documents/{id}/history` | F29 — per-document version history |
- **New endpoints (EV-015 F41)**:
  | Method | Path | Feature |
  |--------|------|---------|
  | POST | `/internal/v1/rebuild/{rebuild_run_id}/promote` | Promote shadow rebuild → live |
- **Source**: RD-016; EV-001 / ADR-014; EV-002; EV-015 / ADR-040

### Database app

- **Purpose**: Schema migrations, pgvector extension, seed corpus, privacy regression tests;
  **document store + revision/shadow metadata** (F41).
- **Inputs**: Alembic revisions.
- **Outputs**: Applied schema; forbidden-table CI checks.
- **Source**: feature-list F13–F15; ADR-004

### Modal FastEmbed & LLM services

- **Purpose**: Self-hosted embedding (384-dim) and text generation.
- **Inputs**: Text / chat payloads over HTTP.
- **Outputs**: Vectors or completions/streams.
- **Note**: **vLLM primary** on Modal (ADR-009); sole LLM deployable is **`vecinita-llm`** (ADR-037). Ollama Modal app deprecated.
- **Source**: ADR-002, ADR-004, ADR-037

### LLM client + prompt helper (F39 follow-on, RD-163–RD-172)

- **Purpose**: Single HTTP client for all `vecinita-llm` routes; shared chat-template wrapping; catalog gated by HF registry.
- **Components**:
  | Component | Location | Change |
  |-----------|----------|--------|
  | Unified client | `packages/llm-client` | Merge `LlmClient` + `OllamaModelsClient` (generate/stream/warm + list/pull); one env/auth/timeout resolver |
  | Playground types | `packages/shared-schemas` | Rename `ollama_*` → `playground_*` (compat re-exports optional); path aliases stay `/models/ollama` |
  | Modal ASGI | `infra/modal/llm_app.py` | Real vLLM `stream_tokens`; proxy auth on generate/warm; later separate playground class (slice D) |
  | Chat-template helper | Prefer `packages/llm-client` (or shared-schemas) | HF `apply_chat_template`; used by chat-rag, tagging, eval |
- **Prod pin**: Default model `qwen2.5:1.5b-instruct` / `Qwen/Qwen2.5-1.5B-Instruct` on prod class; playground overrides only on playground class.
- **Out of scope**: Provider ABC / multi-provider plugin framework.
- **Source**: S010 / EV-011 RD-163–RD-172; ADR-037 amendment

### Frontend i18n (`packages/frontend-i18n`) — EV-004 F31

- **Purpose**: Pure TypeScript locale utilities and EN/ES message tables shared by both browser SPAs.
- **Inputs**: Browser `navigator.language`; optional `localStorage` value at key `vecinita.locale`.
- **Outputs**: Resolved `Locale` (`en` \| `es`); translated strings via `t(locale, key, ...)` with dot-prefixed keys (`chat.*`, `admin.*`, `shared.*`).
- **Algorithm**:
  1. On load: read `vecinita.locale` from `localStorage` if valid.
  2. Else `detectBrowserLocale()`: `en*` → `en`, `es*` → `es`, otherwise **ES**.
  3. Persist user selection back to `vecinita.locale` (shared across apps on same browser profile).
- **Error handling**: Unknown message keys fail at compile time (typed keys); runtime missing key returns key string (dev guard).
- **Source**: ADR-019; feature-list F31

### Frontend UI (`packages/frontend-ui`) — EV-004 F31

- **Purpose**: Shared React + Tailwind components for consistent bilingual UX across ChatRAG and admin.
- **Exports**: `LocaleProvider`, `useLocale`, `LanguageToggle`, `ThemeToggle`, `TagFilterChips`, `TagBadge`, `PaginationControls`; minimal shadcn re-exports (`Button`, `Badge`, `Input`, `Label`, `Dialog`).
- **Inputs**: React tree wrapped in `LocaleProvider`; components read locale via `useLocale()`.
- **Outputs**: Accessible UI controls; sets `document.documentElement.lang` on locale change.
- **Styling**: Tailwind CSS in package; admin consumes directly; ChatRAG migrates layout to Tailwind in EV-004.
- **Dependency rule**: Depends on `frontend-i18n` only; must not import `apps/*`.
- **Source**: ADR-020 (amended); feature-list F31

### Admin authentication (Supabase Auth) — EV-005 F34

- **Purpose**: Authenticate **operators** on the admin surfaces using **Supabase Auth**; gate the DM UI, DM API, and internal-write API. ChatRAG stays anonymous. Supersedes the ADR-004 infra-only admin protection (F16) for these surfaces (ADR-026).
- **Identity provider**: Supabase project (canonical ref `cfuvghdsuwactfeamtym`, per `prod.env`; MCP access to be granted — R53). Operator identity/PII (email, name, password, invites) live **only** in Supabase `auth.*`; the Vecinita corpus DB stays PII-free.
- **Registration**: **Invitation-only** — public sign-up disabled in Supabase; an `admin` invites by email; the invitee accepts via emailed link and sets a password. Login is **email + password** (RD-074).
- **Roles**: `admin` (full read/write) and `viewer` (read-only), carried as a Supabase JWT claim (mechanism — `app_metadata` claim vs `user_roles` — decided in 04-tech-plan). Writes require `admin`; `viewer` → `403` (RD-075).
- **Frontend (`apps/data-management-frontend`)**: `@supabase/supabase-js` browser session (SPA); login screen; protected routes (redirect to login when no session); current-user display + logout. Sends `Authorization: Bearer <supabase_jwt>` to admin APIs (RD-076).
- **Backends (`apps/data-management-backend`, `apps/internal-write-api`)**: A FastAPI dependency verifies the Supabase JWT on each request; `401` on missing/invalid/expired token; role check for write routes (`403` for `viewer`). Service-to-service Modal→internal-write calls continue to use the existing `VECINITA_INTERNAL_API_KEY` (machine credential), distinct from operator JWTs.
- **Audit attribution**: write helpers record `actor_id` (opaque Supabase user UUID) + `actor_role` on `audit_log` — no PII (extends ADR-016).
- **Environment syncing**: Supabase **branching** (preview/staging via Git) on the canonical project; auth/schema migrations in repo; secrets via Modal/DO env, never tracked (RD-078, no-operator-spec-commits).
- **ChatRAG CORS (anonymous, tightened)**: ChatRAG API restricts CORS to the **ChatRAG frontend origin only** (RD-079); admin APIs add `Authorization` to allowed headers.
- **Source**: feature-list F34; ADR-026; context-brief §15; RD-073–RD-079

## Data Flow

| Stage | Input | Transformation | Output | Notes |
|-------|--------|----------------|--------|-------|
| 1. Submit scrape job | URL list | Admin UI → Modal ASGI `POST /jobs` | job_id | Infra auth only |
| 2. Scrape | job_id, URLs | Modal worker fetches HTML | raw text | No PII stored |
| 3. Hash gate | body + stored hash | Skip chunks/embed if unchanged (unless `force`) | skip or continue | F47 |
| 4. Chunk | raw text | HF tokenizer + `chunk_size` / `chunk_overlap` | chunk records | F49 / ADR-044 |
| 5. LLM tag | chunks + seed vocab | Modal LLM | document/chunk tags (`llm`) | Max 10/5 tags; ADR-023 |
| 6. Embed | chunks | Modal FastEmbed (sub-batch + retry) | 384-dim vectors | F48 |
| 7. Persist | chunks + vectors + tags | Modal → **DO internal write API** | Postgres rows | **No Modal DATABASE_URL** |
| 8. Browse | tag/search filters | ChatRAG GET APIs | document list | Public |
| 9. Query | user question + optional tags | ChatRAG Backend | — | Stateless |
| 10. Resolve tags | tags[] or question | User tags OR LLM infer | tag filter set | User tags win if set |
| 11. Embed query | question text | Modal FastEmbed | query vector | — |
| 12. Retrieve | query vector + tags | pgvector + tag JOIN | top_k chunks | Union doc+chunk tags |
| 13. Generate | context + question | Modal LLM | answer / stream | No server chat history |
| 14. Record stats | response doc IDs | ChatRAG → internal write API `POST /stats/served` | serving counter++ | Async fire-and-forget (F28) |
| 15. Emit audit | write operation | Internal write API middleware | audit_log row | Immutable, request_id only (F29) |

### Query path (detail)

```
Browser → DO ChatRAG Backend → (F43 cache hit? return)
         → Modal FastEmbed → DO pgvector read
         → packages/rag (F44 L1? → H7 merge → F45 CE? → P1 pack)
         → Modal LLM (stream) → Browser (+ populate F43 stores)
```

F36 eval sandbox must call the same `packages/rag` packer + H7 helpers (no parallel prompt assembly).
F43 cache and F44/F45 flags apply on ChatRAG; harness measures cost/hit-rate and CE gate.

### Ingest path (detail)

```
Admin UI → Modal ASGI (/jobs) → Modal queue worker → scrape → chunk → FastEmbed
         → DO internal write API → Postgres
```

## Constraints & Assumptions

### Hard Constraints

| ID | Constraint | Source |
|----|------------|--------|
| H1 | Five applications, separate deploy boundaries | ADR-001 |
| H2 | Hybrid Modal + DigitalOcean; US regions only | ADR-002, R10a |
| H3 | Greenfield APIs; OpenAPI required as source of truth | ADR-003, user interview |
| H4 | DO Managed Postgres + pgvector; 384-dim default | ADR-005, ADR-008 |
| H5 | Zero personal data **in the corpus DB** — no user/admin/session/message tables, no server chat history. **Admin-surface operator identity lives in Supabase only** (EV-005 F34); corpus DB may store only an opaque Supabase user UUID + role for audit attribution | ADR-004, **ADR-026** |
| H11 | **Admin surfaces require Supabase JWT** (DM UI/API, internal-write API); ChatRAG stays anonymous; invite-only registration; `admin`/`viewer` roles | ADR-026 (EV-005 F34) |
| H6 | No paid third-party LLM/embed APIs as default | ADR-004, ADR-008, ADR-009 |
| H7 | Cost ≤ $50/mo cap (target $25) | ADR-004, ADR-010 |
| H8 | Only DO backends hold `DATABASE_URL` | ADR-007 |
| H9 | `packages/` must not import `apps/` | ADR-012 |
| H10 | Python **3.11** / Node **24 LTS** (dependency-inventory.md; TP-S004-11) | 04-tech-plan |

### Forbidden schema (minimum deny-list)

Migrations and CI must reject tables/columns including:

`users`, `accounts`, `sessions`, `messages`, `profiles`, `invites`, `auth_*`

Allowed domains: `documents`, `chunks`, `embeddings`, `jobs`, `config`, `tags`, `document_tags`, `chunk_tags` (EV-001), `audit_log`, `document_versions`, `document_serving_stats` (EV-002). Tag provenance: `source` enum only — no operator identity columns. Audit log: `request_id` only — no IP/identity columns (ADR-016).

**EV-005 (F34) exception (corpus DB):** `audit_log` may add `actor_id` (opaque **Supabase user UUID**) + `actor_role` (`admin`/`viewer`) columns for attribution — **both non-PII**. No `email`/`name`/`password` column is permitted in the corpus DB. The forbidden list (`users`, `accounts`, `sessions`, `messages`, `profiles`, `invites`, `auth_*`) still applies to the corpus DB; Supabase manages its own `auth.*` schema in a **separate** database (ADR-026).

### Assumptions

- Operators access data-mgmt via platform secrets or private network, not Vecinita login.
- Corpus content is **public** community material (URLs, public documents).
- Bilingual behavior: **auto-detect** query language and respond in the same language.
- Local dev uses **docker-compose + Modal serve** (full stack).

### Soft / deferred

| Topic | Status |
|-------|--------|
| Dedicated API gateway (R6) | **Deferred** — direct backend URLs in v1 (TP-001) |
| vLLM model / GPU | **Qwen2.5-1.5B-Instruct** on Modal **T4**; Ollama fallback if cost fails after DO consolidation |
| Full OCR / multimodal beyond basic PDF text | Post-v1 (F59 covers best-effort PDF text) |
| ChatRAG nested corpus UI | Deferred — licensing research (S024-D17) |

## API surface (summary)

| Service | Method | Path | Notes |
|---------|--------|------|-------|
| ChatRAG | POST | `/api/v1/ask` | Non-streaming Q&A; optional `tags[]` |
| ChatRAG | POST | `/api/v1/ask/stream` | SSE streaming; optional `tags[]` |
| ChatRAG | GET | `/api/v1/documents` | Public browse (tags, q, pagination) |
| ChatRAG | GET | `/api/v1/documents/{id}` | Public document detail + tags |
| ChatRAG | GET | `/api/v1/tags` | Public tag list (facets) |
| Internal write | GET | `/internal/v1/documents/{id}/chunks` | Admin chunk list |
| Internal write | PATCH | `/internal/v1/documents/{id}/tags` | Admin document tags |
| Internal write | PATCH | `/internal/v1/chunks/{id}/tags` | Admin chunk tags |
| Internal write | POST | `/internal/v1/documents/{id}/retag` | Admin LLM re-tag (proposed) |
| Data Mgmt (Modal) | POST/GET | `/jobs`, `/jobs/{id}` | Proxy auth; crawl options F60 |
| Internal write | GET | `/internal/v1/corpus/tree` | Nested corpus hierarchy (F61) |
| Data Mgmt (Modal) | GET | `/jobs/{id}/tree` | Job result tree nodes (F60/F61) |
| Internal write | GET | `/internal/v1/stats/summary` | Dashboard aggregated stats (F25) |
| Internal write | POST | `/internal/v1/stats/served` | Increment serving counter (F28) |
| Internal write | GET | `/internal/v1/stats/top-served` | Top served documents (F28) |
| Internal write | DELETE | `/internal/v1/documents/bulk` | Bulk delete (F27) |
| Internal write | PATCH | `/internal/v1/documents/bulk/tags` | Bulk tag (F27) |
| Internal write | POST | `/internal/v1/documents/bulk/retag` | Bulk LLM re-tag (F27) |
| Internal write | PATCH | `/internal/v1/documents/bulk/metadata` | Bulk edit metadata (F27) |
| Internal write | GET | `/internal/v1/audit` | Global audit log (F29) |
| Internal write | GET | `/internal/v1/documents/{id}/history` | Per-document history (F29) |
| Internal write | POST | `/internal/v1/rebuild/{rebuild_run_id}/promote` | Promote shadow rebuild (F41) |
| Internal write | GET | `/internal/v1/health/all` | Health aggregator — polls all 8 services (F26, TP-019) |
| Health | GET | `/health` | All HTTP services |

Full schemas: `docs/api-contract.md`; OpenAPI files in repo (required).

**Auth (EV-005 F34):** Admin surfaces — Data Management API (Modal `/jobs`) and the **internal-write API** (`/internal/v1/*`) — require a valid **Supabase JWT** via `Authorization: Bearer` (`401` missing/invalid; `403` for `viewer` on writes). ChatRAG routes (`/api/v1/*`) stay **anonymous** with CORS restricted to the ChatRAG frontend origin. Modal→internal-write service calls keep the existing `VECINITA_INTERNAL_API_KEY`. Details: `docs/api-contract.md` §Authentication (ADR-026).

## Session changelog

| Session / cycle | Date | Change |
|-----------------|------|--------|
| S004 / EV-005 (F34) | 2026-06-28 | Added admin Supabase Auth: §Component Details "Admin authentication"; H5 amended + H11 added; forbidden-schema EV-005 exception (`actor_id`/`actor_role`); API surface auth note. Supersedes ADR-004 admin auth clause (ADR-026). |
| S017 / EV-015 (F41) | 2026-07-30 | Document store + rebuild job (`reembed`/`rechunk`/`rescrape`); shadow dry-run + promote; version stamps (ADR-040). |
| S019 / EV-016 (F42) | 2026-08-01 | H7+P1 on E0: heuristic multi-query + Source/URL packing in `packages/rag` (ADR-041); ChatRAG + F36 share helpers; P3 config-gated off; no LangGraph / no embed swap. |
| S023 / EV-020 (F50–F51) | 2026-08-02 | Prod defaults: `top_k=8` (F50/#158); packer `p3` (F51/#165); sources shown = retrieve count; no adaptive top_k / no CE enable. |
| S020 / EV-017 (F43–F45) | 2026-08-02 | H1 cache cascade (F43); config-gated L1 soft language (F44); CE spike+gate with `bge-reranker-v2-m3` (F45); no LangGraph / ADR-006 amend. |
| S021 / EV-018 (F46 + F45) | 2026-08-02 | Staging retrieve reliability (F46 non-empty pools); F45 CE re-gate only after F46; prod CE stays off until AC-BB9. |
| S022 / EV-019 (F47–F49) | 2026-08-02 | Ingest resilience: content_hash skip + metadata refresh (F47); embed sub-batch/retry fail-URL (F48); HF tokenizer + overlap default 32 (F49 / ADR-044). |
| S024 / EV-022 (F59–F61) | 2026-08-03 | Robust scrape + JS-render + PDF text (F59); website crawl (F60); admin corpus tree + ChatRAG backend nested meta (F61); epic #185. |

## References

- [feature-list.md](feature-list.md)
- [context-brief.md](sessions/S000-internal-docs-archive/context-brief.md)
- [ADR index](adr/README.md) — ADR-001 through ADR-016
- [decisions.md#Requirements decisions](decisions.md#requirements-decisions-01-requirements)
