# 03 — Service Profiles

> Auto-generated: 2026-05-12

## chat-frontend

| Attribute | Value |
|-----------|-------|
| **Purpose** | End-user chat interface for RAG-powered Q&A |
| **Owner** | Solo developer |
| **Users** | Community members seeking civic information |
| **Stack** | React, Vite, TypeScript |
| **Deploy** | Render web service |
| **Criticality** | Tier 1 (user-facing) |
| **Current path** | `frontends/chat/` (submodule) |
| **Target path** | `apps/chat-frontend/` |

## data-management-frontend

| Attribute | Value |
|-----------|-------|
| **Purpose** | Admin UI for managing scraped data, documents, corpus |
| **Owner** | Solo developer |
| **Users** | Admin/developer |
| **Stack** | React, Vite, TypeScript |
| **Deploy** | Render web service |
| **Criticality** | Tier 2 (admin tool) |
| **Current path** | `frontends/data-management/` (submodule) |
| **Target path** | `apps/data-management-frontend/` |

## docs-site

| Attribute | Value |
|-----------|-------|
| **Purpose** | Project documentation site |
| **Owner** | Solo developer |
| **Users** | Developers, contributors |
| **Stack** | Static site generator |
| **Deploy** | Render web / GitHub Pages |
| **Criticality** | Tier 3 (documentation) |
| **Current path** | `docs-site/` |
| **Target path** | `apps/docs-site/` |

## gateway

| Attribute | Value |
|-----------|-------|
| **Purpose** | HTTP entry point. Auth, CORS, rate limiting, routing, job orchestration, data CRUD, streaming |
| **Owner** | Solo developer |
| **Users** | All frontend apps, external consumers |
| **Stack** | Python, FastAPI |
| **Deploy** | Render web service |
| **Criticality** | Tier 1 (all traffic flows through it) |
| **Current path** | `apis/gateway/` |
| **Target path** | `apps/gateway/` |

## agent

| Attribute | Value |
|-----------|-------|
| **Purpose** | RAG brain. LlamaIndex pipeline, conversations, tool calling, vector search |
| **Owner** | Solo developer |
| **Users** | Gateway (internal service-to-service) |
| **Stack** | Python, FastAPI, LlamaIndex, pgvector |
| **Deploy** | Render web service |
| **Criticality** | Tier 1 (core AI functionality) |
| **Current path** | `apis/agent/` + `apis/gateway/src/agent/` |
| **Target path** | `apps/agent/` |

## data-management-api

| Attribute | Value |
|-----------|-------|
| **Purpose** | CRUD for scraped documents, corpus management, metadata |
| **Owner** | Solo developer |
| **Users** | data-management-frontend, gateway |
| **Stack** | Python, FastAPI |
| **Deploy** | Render web service |
| **Criticality** | Tier 2 (data management) |
| **Current path** | `apis/data-management-api/` (submodule) |
| **Target path** | `apps/data-management-api/` |

## pgadmin

| Attribute | Value |
|-----------|-------|
| **Purpose** | PostgreSQL management UI |
| **Owner** | Solo developer |
| **Users** | Developer (internal only) |
| **Stack** | PgAdmin 4 Docker image |
| **Deploy** | Render private service |
| **Criticality** | Tier 3 (developer tool) |
| **Current path** | docker-compose only |
| **Target path** | `apps/pgadmin/` |

## vllm-inference

| Attribute | Value |
|-----------|-------|
| **Purpose** | LLM inference via vLLM on GPU, OpenAI-compatible API |
| **Owner** | Solo developer |
| **Users** | Agent (via LlamaIndex) |
| **Stack** | Python, vLLM, Modal |
| **Deploy** | Modal serverless GPU |
| **Criticality** | Tier 1 (core AI inference) |
| **Current path** | `modal-apps/model-modal/` (rewrite) |
| **Target path** | `apps/vllm-inference/` |

## embedding-worker

| Attribute | Value |
|-----------|-------|
| **Purpose** | Batch text embedding for RAG pipeline via LlamaIndex |
| **Owner** | Solo developer |
| **Users** | Gateway (triggered via Modal SDK) |
| **Stack** | Python, LlamaIndex, Modal |
| **Deploy** | Modal serverless GPU |
| **Criticality** | Tier 1 (RAG pipeline dependency) |
| **Current path** | `modal-apps/embedding-modal/` (rewrite) |
| **Target path** | `apps/embedding-worker/` |

## scraper-worker

| Attribute | Value |
|-----------|-------|
| **Purpose** | Web scraping and content extraction as background jobs |
| **Owner** | Solo developer |
| **Users** | Gateway (triggered via Modal SDK) |
| **Stack** | Python, Modal |
| **Deploy** | Modal serverless |
| **Criticality** | Tier 2 (data ingestion) |
| **Current path** | `modal-apps/scraper/` (submodule) |
| **Target path** | `apps/scraper-worker/` |

## indexing-worker

| Attribute | Value |
|-----------|-------|
| **Purpose** | Document indexing pipeline: single-doc, batch, selective re-index, full rebuild |
| **Owner** | Solo developer |
| **Users** | Gateway (triggered via Modal SDK) |
| **Stack** | Python, LlamaIndex, Modal |
| **Deploy** | Modal serverless |
| **Criticality** | Tier 2 (maintenance) |
| **Current path** | New |
| **Target path** | `apps/indexing-worker/` |
