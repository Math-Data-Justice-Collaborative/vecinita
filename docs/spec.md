# Technical Specification

> **Project**: Vecinita  
> **Repository**: `/root/GitHub/VECINA/vecinita`  
> **Version**: greenfield (`fresh-start` branch)  
> **Last updated**: 2026-05-19

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
| Data Management Frontend | Jobs + corpus admin UI | `apps/data-management-frontend` | Modal ASGI (+ DO routes if needed) |
| Database app | Alembic, pgvector, seeds, privacy tests | `apps/database` | Postgres |
| Internal write API | Upsert documents/chunks/embeddings; corpus CRUD | DO App Platform (**standalone** service) | Postgres only |
| Shared RAG | LlamaIndex pipelines | `packages/rag` | LlamaIndex, pgvector client |
| Shared ingest | Scrape/chunk helpers | `packages/ingest` | — |
| Embedding client | HTTP client to Modal FastEmbed | `packages/embedding-client` | Modal |

**Package rule (RD-014):** `packages/*` must not import `apps/*`; apps depend on packages only.

## Component Details

### ChatRAG Backend

- **Purpose**: Stateless bilingual Q&A with retrieval and streaming generation.
- **Inputs**: `POST /api/v1/ask`, `POST /api/v1/ask/stream` (JSON body: question text; optional client metadata without identity fields).
- **Outputs**: Answer JSON or SSE token stream; source chunk references (IDs, not PII).
- **Algorithm**:
  1. Auto-detect query language (en/es).
  2. Embed query via Modal FastEmbed (HTTP).
  3. pgvector similarity search (top_k) on DO Postgres.
  4. LlamaIndex synthesize with retrieved context.
  5. Stream or return completion via Modal LLM HTTP.
- **Key parameters**: See `docs/config-spec.md` (pending): `top_k`, model names, timeouts.
- **Error handling**: 4xx for validation (including rejected identity fields); 5xx with request ID in logs (no raw prompt persistence).
- **Latency**: Target **p95 < 15s** excluding cold start (RD-017).
- **Source**: feature-list F1–F6; user interview 01-requirements

### ChatRAG Frontend

- **Purpose**: Public chat UI; client-side conversation state only.
- **Inputs**: User messages in browser.
- **Outputs**: Rendered answers; calls streaming endpoint.
- **Source**: feature-list F11

### Data Management (Modal ASGI + workers)

- **Purpose**: Operator-triggered ingest jobs and job status; no Vecinita user accounts.
- **Inputs**: `POST /jobs` (URLs, options); `GET /jobs/{id}`; protected by Modal `requires_proxy_auth` + deploy secret at edge.
- **Outputs**: Job records (URL, status, error codes — no operator identity).
- **Algorithm** (ingest):
  1. ASGI enqueues scrape job on Modal queue.
  2. Worker fetches URL, normalizes HTML/text.
  3. Chunk text; call FastEmbed on Modal.
  4. **POST chunks/embeddings to DO internal write API** (not direct Postgres).
  5. Update job status via DO API or job store on DO.
- **Source**: feature-list F7–F10; RD-016

### DO internal write API

- **Purpose**: Sole component(s) with `DATABASE_URL`; accepts service-authenticated writes from Modal.
- **Inputs**: Authenticated requests (mTLS, API key, or private network) with document/chunk/embedding payloads.
- **Outputs**: Upserted rows; corpus list/delete for admin.
- **Source**: RD-016 contradiction resolution

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

## Data Flow

| Stage | Input | Transformation | Output | Notes |
|-------|--------|----------------|--------|-------|
| 1. Submit scrape job | URL list | Admin UI → Modal ASGI `POST /jobs` | job_id | Infra auth only |
| 2. Scrape | job_id, URLs | Modal worker fetches HTML | raw text | No PII stored |
| 3. Chunk | raw text | Split per config `chunk_size` | chunk records | — |
| 4. Embed | chunks | Modal FastEmbed | 384-dim vectors | — |
| 5. Persist | chunks + vectors | Modal → **DO internal write API** | Postgres rows | **No Modal DATABASE_URL** |
| 6. Query | user question | ChatRAG Backend | — | Stateless |
| 7. Embed query | question text | Modal FastEmbed | query vector | — |
| 8. Retrieve | query vector | pgvector on DO | top_k chunks | LlamaIndex retriever |
| 9. Generate | context + question | Modal LLM | answer / stream | No server chat history |

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

Allowed domains: `documents`, `chunks`, `embeddings`, `jobs`, `config` (and operational non-PII metadata).

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
| ChatRAG | POST | `/api/v1/ask` | Non-streaming Q&A |
| ChatRAG | POST | `/api/v1/ask/stream` | SSE streaming |
| Data Mgmt (Modal) | POST/GET | `/jobs`, `/jobs/{id}` | Proxy auth |
| Health | GET | `/health` | All HTTP services |

Full schemas: `docs/api-contract.md` (interview pending); OpenAPI files in repo (required).

## References

- [feature-list.md](feature-list.md)
- [context-brief.md](context-brief.md)
- [ADR index](adr/README.md) — ADR-001 through ADR-013
- [requirements-decisions.md](requirements-decisions.md)
