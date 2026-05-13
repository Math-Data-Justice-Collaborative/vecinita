# 01 — Executive Summary

> Auto-generated: 2026-05-12

## Current State

Vecinita is a RAG-powered civic/community information chat agent built as a
monorepo with 6 git submodules. The current layout mixes `apis/`, `frontends/`,
`modal-apps/`, `packages/`, `clients/`, and `infrastructure/` directories with
no consistent service boundary pattern.

### Key problems

| Problem | Impact |
|---------|--------|
| Git submodules add friction to development | Every change requires coordinating commits across repos |
| Gateway service is a monolith | Contains agent logic, embedding, scraper routing, LLM routing, DB services, corpus management, ingestion, Modal orchestration |
| No clear data ownership | Single shared DB with no schema separation |
| 5 docker-compose files | Unclear which to use, configuration drift between environments |
| 17 CI workflows | Slow, hard to maintain, unclear which services they cover |
| Scattered .env files | 19 env files across the tree, no single source of truth |

## Proposed Target State

Convert to a true `apps/` + `packages/` monorepo with:

- **12 deployable apps** in `apps/` (Render web services, Modal GPU workers, database)
- **3 shared packages** in `packages/` (DB models, config utilities, common types)
- **Per-service env files** in `.environments/`
- **Single `render.yaml`** at root for all Render-deployed services
- **Single `docker-compose.yml`** with profiles for local development
- **Schema-per-service** PostgreSQL (logical separation, one instance)
- **vLLM on Modal** for LLM inference, integrated via LlamaIndex
- **LlamaIndex** for RAG pipeline (embedding + indexing + retrieval)
- **Modal Job Queues** for all background work (scraping, embedding, reindexing)

## Service Count

| Category | Count | Runtime |
|----------|-------|---------|
| Frontend apps | 3 | Render (chat, data-management, docs-site) |
| Backend API services | 3 | Render (gateway, agent, data-management-api) |
| Infrastructure services | 1 | Render private (pgadmin) |
| GPU workers | 2 | Modal (vllm-inference, embedding-worker) |
| Background workers | 2 | Modal (scraper-worker, indexing-worker) |
| Database | 1 | Render (postgres) |
| **Total** | **12** | |

## Technical Decisions Made

| ID | Decision | Choice |
|----|----------|--------|
| TD-001 | Directory layout | `apps/` + `packages/` |
| TD-002 | Database strategy | Schema-per-service (logical separation) |
| TD-003 | Local dev | Docker Compose with profiles |
| TD-004 | PgAdmin deploy | Render private service |
| TD-005 | CI strategy | One workflow per app (path-filtered) |
| TD-006 | OpenAPI clients | Drop — use simple HTTP clients |
| TD-007 | Python deps | Deferred (defaulting to uv) |
| TD-008 | LLM providers | Deferred (vLLM primary + API fallbacks) |
| TD-009 | Model selection | Deferred (design for flexibility) |

## Recommended Migration Approach

Full rewrite in phases:
1. **Phase 1**: Flatten submodules, establish `apps/` + `packages/` layout
2. **Phase 2**: Restructure gateway (extract agent, simplify routing)
3. **Phase 3**: Integrate vLLM + LlamaIndex (replace Modal model-modal + embedding-modal)
4. **Phase 4**: Schema-per-service migration
5. **Phase 5**: New render.yaml + docker-compose.yml + CI workflows
6. **Phase 6**: Environment consolidation (`.environments/`)
