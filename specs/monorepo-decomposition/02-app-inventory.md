# 02 — App Inventory

> Auto-generated: 2026-05-12

## Apps (Deployable Units)

All apps live under `apps/` in the new monorepo layout.

### Frontend Apps

| App | Purpose | Tech Stack | Deploy Target | Current Location | Submodule? |
|-----|---------|-----------|---------------|-----------------|------------|
| `chat-frontend` | End-user chat interface for RAG-powered Q&A | React, Vite, TypeScript | Render web | `frontends/chat/` | Yes |
| `data-management-frontend` | Admin UI for managing scraped data, documents, corpus | React, Vite, TypeScript | Render web | `frontends/data-management/` | Yes |
| `docs-site` | Project documentation site | Static site generator | Render web / GitHub Pages | `docs-site/` | No |

### Backend API Services

| App | Purpose | Tech Stack | Deploy Target | Current Location | Submodule? |
|-----|---------|-----------|---------------|-----------------|------------|
| `gateway` | HTTP routing, auth, CORS, rate limiting, request orchestration, scraper/embedding job triggers, data CRUD, websocket streaming, OpenAPI aggregation | Python, FastAPI | Render web | `apis/gateway/` | No |
| `agent` | RAG/LLM logic via LlamaIndex, conversation management, tool calling, vector search | Python, FastAPI, LlamaIndex | Render web | `apis/agent/` + `apis/gateway/src/agent/` | Partial |
| `data-management-api` | CRUD for scraped data, document management, corpus operations | Python, FastAPI | Render web | `apis/data-management-api/` + `modal-apps/scraper/` | Yes |

### Infrastructure Services

| App | Purpose | Tech Stack | Deploy Target | Current Location | Submodule? |
|-----|---------|-----------|---------------|-----------------|------------|
| `pgadmin` | PostgreSQL management UI (private, internal only) | PgAdmin 4 (Docker image) | Render private service | docker-compose only | No |

### GPU Workers (Modal)

| App | Purpose | Tech Stack | Deploy Target | Current Location | Submodule? |
|-----|---------|-----------|---------------|-----------------|------------|
| `vllm-inference` | LLM inference engine serving OpenAI-compatible API | Python, vLLM, Modal | Modal serverless GPU | `modal-apps/model-modal/` (rewrite) | Yes |
| `embedding-worker` | Batch text embedding for RAG pipeline | Python, LlamaIndex, Modal | Modal serverless GPU | `modal-apps/embedding-modal/` (rewrite) | Yes |

### Background Workers (Modal)

| App | Purpose | Tech Stack | Deploy Target | Current Location | Submodule? |
|-----|---------|-----------|---------------|-----------------|------------|
| `scraper-worker` | Web scraping and content extraction | Python, Modal | Modal serverless | `modal-apps/scraper/` | Yes |
| `indexing-worker` | Document indexing pipeline: single-doc, batch, selective re-index, full rebuild | Python, LlamaIndex, Modal | Modal serverless | New | N/A |

### Database

| App | Purpose | Tech Stack | Deploy Target | Current Location |
|-----|---------|-----------|---------------|-----------------|
| `postgres` | Primary data store (schema-per-service) | PostgreSQL 16, pgvector | Render managed | `render.yaml` database section |

## Packages (Shared Libraries)

All packages live under `packages/` in the new monorepo layout.

| Package | Purpose | Consumers | Current Location |
|---------|---------|-----------|-----------------|
| `db` | Database models, migrations, connection utilities, shared schema definitions | gateway, agent, data-management-api | `packages/python/db` |
| `config` | Shared configuration loading, env var parsing, validation | All Python apps | Scattered across services |
| `common` | Shared types, constants, error classes used across services | All Python apps | New (extracted from gateway) |

## Migration Map

| Current Path | New Path | Action |
|-------------|----------|--------|
| `frontends/chat/` | `apps/chat-frontend/` | Move, deinit submodule |
| `frontends/data-management/` | `apps/data-management-frontend/` | Move, deinit submodule |
| `docs-site/` | `apps/docs-site/` | Move |
| `apis/gateway/` | `apps/gateway/` | Move, refactor |
| `apis/agent/` + `apis/gateway/src/agent/` | `apps/agent/` | Consolidate, refactor |
| `apis/data-management-api/` | `apps/data-management-api/` | Move, deinit submodule |
| (docker-compose pgadmin) | `apps/pgadmin/` | New config dir |
| `modal-apps/model-modal/` | `apps/vllm-inference/` | Rewrite with vLLM |
| `modal-apps/embedding-modal/` | `apps/embedding-worker/` | Rewrite with LlamaIndex |
| `modal-apps/scraper/` | `apps/scraper-worker/` | Refactor, deinit submodule |
| (new) | `apps/indexing-worker/` | New service |
| `packages/python/db` | `packages/db/` | Move |
| `packages/openapi-clients/` | (removed) | Drop per TD-006 |
| (scattered config) | `packages/config/` | New, extracted |
| (scattered types) | `packages/common/` | New, extracted |
