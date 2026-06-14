# Technical Specification

> **Project**: Vecinita  
> **Repository**: `/root/GitHub/VECINA/vecinita`  
> **Version**: greenfield (`fresh-start` branch)  
> **Last updated**: 2026-06-13 (EV-004 F31 delta)

## Overview

Vecinita is a **five-application monorepo** delivering a **bilingual (English/Spanish) community Q&A RAG chatbot** (ChatRAG) and a **data management platform** (scrape, chunk, embed, corpus admin). Deployment is **hybrid**: DigitalOcean hosts HTTP APIs that touch Postgres, both React frontends, and managed Postgres; **Modal** hosts async ingest workers, FastEmbed, **vLLM** (primary LLM per ADR-009), and the **Data Management ASGI API** (`requires_proxy_auth`). RAG orchestration uses **LlamaIndex** in `packages/rag`. The system enforces **zero personal data**, **US-only** infrastructure, and a **≤ $50/month** cost cap (target $25) per ADR-004.

## System Architecture

Five deployable applications share Postgres (pgvector) and internal packages. **Only DigitalOcean backends hold `DATABASE_URL`**; Modal workers persist data by calling a **DO internal write API** (RD-016).

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
| Shared RAG | LlamaIndex pipelines | `packages/rag` | LlamaIndex, pgvector client |
| Shared ingest | Scrape/chunk helpers | `packages/ingest` | — |
| Embedding client | HTTP client to Modal FastEmbed | `packages/embedding-client` | Modal |
| Shared tagging | LLM/human tag prompts, vocabulary merge, cap enforcement | `packages/tagging` | Modal LLM (vLLM), config-spec |
| **Frontend i18n** | Locale detection, storage, EN/ES message tables (`t()`) | `packages/frontend-i18n` | None (pure TS) — EV-004 F31 |
| **Frontend UI** | Shared React locale provider, language toggle, tag/pagination primitives | `packages/frontend-ui` | `frontend-i18n`, Tailwind, minimal shadcn — EV-004 F31 |

**Package rule (RD-014):** `packages/*` must not import `apps/*`; apps depend on packages only.

## Component Details

### ChatRAG Backend

- **Purpose**: Stateless bilingual Q&A with retrieval and streaming generation; **public corpus read** (EV-001).
- **Inputs**: `POST /api/v1/ask`, `POST /api/v1/ask/stream` (JSON: question; optional `tags[]`); **GET** `/api/v1/documents`, `/api/v1/tags`, `/api/v1/documents/{id}` (public browse).
- **Outputs**: Answer JSON or SSE token stream; source chunk references (IDs, not PII).
- **Algorithm**:
  1. Auto-detect query language (en/es).
  2. Embed query via Modal FastEmbed (HTTP).
  3. pgvector similarity search (top_k) on DO Postgres; **optional tag filter** (user-selected or LLM-inferred).
  4. LlamaIndex synthesize with retrieved context.
  5. Stream or return completion via Modal LLM HTTP.
- **Key parameters**: See `docs/config-spec.md` (pending): `top_k`, model names, timeouts.
- **Error handling**: 4xx for validation (including rejected identity fields); 5xx with request ID in logs (no raw prompt persistence).
- **Latency**: Target **p95 < 15s** excluding cold start (RD-017).
- **Source**: feature-list F1–F6; user interview 01-requirements

### ChatRAG Frontend

- **Purpose**: Public chat UI; client-side conversation state only; **corpus browse** and **tag filter sidebar** (EV-001); **bilingual UI chrome** via shared packages (EV-004 F31).
- **Inputs**: User messages in browser; tag chip selection for RAG; browse filters (tags, title/URL search); locale from `vecinita.locale` / browser detect.
- **Outputs**: Rendered answers; calls streaming endpoint; browse list opens **original document URL** in new tab (no in-app reader); UI strings from `packages/frontend-i18n`.
- **Source**: feature-list F11, F19, F22, F31

### Data Management (Modal ASGI + workers)

- **Purpose**: Operator-triggered ingest jobs and job status; no Vecinita user accounts.
- **Inputs**: `POST /jobs` (URLs, options); `GET /jobs/{id}`; protected by Modal `requires_proxy_auth` + deploy secret at edge.
- **Outputs**: Job records (URL, status, error codes — no operator identity).
- **Algorithm** (ingest):
  1. ASGI enqueues scrape job on Modal queue.
  2. Worker fetches URL, normalizes HTML/text.
  3. Chunk text.
  4. **LLM auto-tag** document (and optional chunk tags) from seeded vocabulary + allow new tags (F20).
  5. Call FastEmbed on Modal.
  6. **POST chunks/embeddings/tags to DO internal write API** (not direct Postgres).
  7. Update job status via DO API or job store on DO.
- **Source**: feature-list F7–F10, F20; RD-016

### DO internal write API

- **Purpose**: Sole component(s) with `DATABASE_URL`; accepts service-authenticated writes from Modal; serves stats, audit, bulk operations, and health aggregation (EV-002).
- **Inputs**: Authenticated requests (mTLS, API key, or private network) with document/chunk/embedding/tag payloads; chunk list; tag PATCH; bulk operations (F27); stats increment (F28); audit queries (F29).
- **Outputs**: Upserted rows; corpus list/delete; chunk list; tag CRUD for admin (F21); aggregated stats (F25); audit log entries (F29); serving stats (F28).
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
- **Source**: RD-016; EV-001 / ADR-014; EV-002

### Database app

- **Purpose**: Schema migrations, pgvector extension, seed corpus, privacy regression tests.
- **Inputs**: Alembic revisions.
- **Outputs**: Applied schema; forbidden-table CI checks.
- **Source**: feature-list F13–F15; ADR-004

### Modal FastEmbed & LLM services

- **Purpose**: Self-hosted embedding (384-dim) and text generation.
- **Inputs**: Text / chat payloads over HTTP.
- **Outputs**: Vectors or completions/streams.
- **Note**: **vLLM primary** on Modal (ADR-009); Ollama documented as fallback if cost proof fails in `04-tech-plan`.
- **Source**: ADR-002, ADR-004

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

## Data Flow

| Stage | Input | Transformation | Output | Notes |
|-------|--------|----------------|--------|-------|
| 1. Submit scrape job | URL list | Admin UI → Modal ASGI `POST /jobs` | job_id | Infra auth only |
| 2. Scrape | job_id, URLs | Modal worker fetches HTML | raw text | No PII stored |
| 3. Chunk | raw text | Split per config `chunk_size` | chunk records | — |
| 4. LLM tag | chunks + seed vocab | Modal LLM | document/chunk tags (`llm`) | Max 10/5 tags |
| 5. Embed | chunks | Modal FastEmbed | 384-dim vectors | — |
| 6. Persist | chunks + vectors + tags | Modal → **DO internal write API** | Postgres rows | **No Modal DATABASE_URL** |
| 7. Browse | tag/search filters | ChatRAG GET APIs | document list | Public |
| 8. Query | user question + optional tags | ChatRAG Backend | — | Stateless |
| 9. Resolve tags | tags[] or question | User tags OR LLM infer | tag filter set | User tags win if set |
| 10. Embed query | question text | Modal FastEmbed | query vector | — |
| 11. Retrieve | query vector + tags | pgvector + tag JOIN | top_k chunks | Union doc+chunk tags |
| 12. Generate | context + question | Modal LLM | answer / stream | No server chat history |
| 13. Record stats | response doc IDs | ChatRAG → internal write API `POST /stats/served` | serving counter++ | Async fire-and-forget (F28) |
| 14. Emit audit | write operation | Internal write API middleware | audit_log row | Immutable, request_id only (F29) |

### Query path (detail)

```
Browser → DO ChatRAG Backend → Modal FastEmbed → DO pgvector read
         → packages/rag (LlamaIndex) → Modal LLM (stream) → Browser
```

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
| H5 | Zero personal data — no user/admin tables, no server chat history | ADR-004 |
| H6 | No paid third-party LLM/embed APIs as default | ADR-004, ADR-008, ADR-009 |
| H7 | Cost ≤ $50/mo cap (target $25) | ADR-004, ADR-010 |
| H8 | Only DO backends hold `DATABASE_URL` | ADR-007 |
| H9 | `packages/` must not import `apps/` | ADR-012 |
| H10 | Python **3.11** / Node **20 LTS** (dependency-inventory.md) | 04-tech-plan |

### Forbidden schema (minimum deny-list)

Migrations and CI must reject tables/columns including:

`users`, `accounts`, `sessions`, `messages`, `profiles`, `invites`, `auth_*`

Allowed domains: `documents`, `chunks`, `embeddings`, `jobs`, `config`, `tags`, `document_tags`, `chunk_tags` (EV-001), `audit_log`, `document_versions`, `document_serving_stats` (EV-002). Tag provenance: `source` enum only — no operator identity columns. Audit log: `request_id` only — no IP/identity columns (ADR-016).

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
| Multimodal / PDF ingest | Post-v1 |

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
| Data Mgmt (Modal) | POST/GET | `/jobs`, `/jobs/{id}` | Proxy auth |
| Internal write | GET | `/internal/v1/stats/summary` | Dashboard aggregated stats (F25) |
| Internal write | POST | `/internal/v1/stats/served` | Increment serving counter (F28) |
| Internal write | GET | `/internal/v1/stats/top-served` | Top served documents (F28) |
| Internal write | DELETE | `/internal/v1/documents/bulk` | Bulk delete (F27) |
| Internal write | PATCH | `/internal/v1/documents/bulk/tags` | Bulk tag (F27) |
| Internal write | POST | `/internal/v1/documents/bulk/retag` | Bulk LLM re-tag (F27) |
| Internal write | PATCH | `/internal/v1/documents/bulk/metadata` | Bulk edit metadata (F27) |
| Internal write | GET | `/internal/v1/audit` | Global audit log (F29) |
| Internal write | GET | `/internal/v1/documents/{id}/history` | Per-document history (F29) |
| Internal write | GET | `/internal/v1/health/all` | Health aggregator — polls all 8 services (F26, TP-019) |
| Health | GET | `/health` | All HTTP services |

Full schemas: `docs/api-contract.md` (interview pending); OpenAPI files in repo (required).

## References

- [feature-list.md](feature-list.md)
- [context-brief.md](context-brief.md)
- [ADR index](adr/README.md) — ADR-001 through ADR-016
- [requirements-decisions.md](requirements-decisions.md)
