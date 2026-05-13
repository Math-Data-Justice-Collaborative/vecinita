# 08 — Recommended Boundaries

> Auto-generated: 2026-05-12

## Target Monorepo Layout

```
vecinita/
├── apps/
│   ├── chat-frontend/             # React chat UI (Render web)
│   │   ├── src/
│   │   ├── Dockerfile
│   │   ├── package.json
│   │   └── vite.config.ts
│   ├── data-management-frontend/  # React admin UI (Render web)
│   │   ├── src/
│   │   ├── Dockerfile
│   │   ├── package.json
│   │   └── vite.config.ts
│   ├── docs-site/                 # Documentation (Render web / GH Pages)
│   │   ├── src/
│   │   └── package.json
│   ├── gateway/                   # API gateway (Render web)
│   │   ├── src/
│   │   ├── Dockerfile
│   │   ├── pyproject.toml
│   │   └── uv.lock
│   ├── agent/                     # RAG agent (Render web)
│   │   ├── src/
│   │   ├── Dockerfile
│   │   ├── pyproject.toml
│   │   └── uv.lock
│   ├── data-management-api/       # Data CRUD (Render web)
│   │   ├── src/
│   │   ├── Dockerfile
│   │   ├── pyproject.toml
│   │   └── uv.lock
│   ├── pgadmin/                   # DB admin (Render private)
│   │   └── config/                # pgAdmin server config
│   ├── vllm-inference/            # LLM inference (Modal GPU)
│   │   ├── main.py
│   │   └── pyproject.toml
│   ├── embedding-worker/          # Batch embedding (Modal GPU)
│   │   ├── main.py
│   │   └── pyproject.toml
│   ├── scraper-worker/            # Web scraping (Modal)
│   │   ├── src/
│   │   └── pyproject.toml
│   └── indexing-worker/            # Indexing pipeline (Modal)
│       ├── main.py
│       └── pyproject.toml
├── packages/
│   ├── db/                        # Shared DB models + migrations
│   │   ├── models/
│   │   ├── migrations/
│   │   └── pyproject.toml
│   ├── config/                    # Shared config loading
│   │   ├── loader.py
│   │   └── pyproject.toml
│   └── common/                    # Shared types + constants
│       ├── types.py
│       ├── errors.py
│       └── pyproject.toml
├── .environments/
│   ├── gateway.env
│   ├── agent.env
│   ├── data-management-api.env
│   ├── chat-frontend.env
│   ├── data-management-frontend.env
│   ├── pgadmin.env
│   ├── vllm-inference.env
│   ├── embedding-worker.env
│   ├── scraper-worker.env
│   └── indexing-worker.env
├── infrastructure/
│   ├── docker/                    # Shared Dockerfiles / base images
│   └── deploy/                    # Deploy scripts
├── scripts/                       # Operational scripts
├── tests/                         # Integration / E2E tests
├── .github/
│   └── workflows/                 # Per-app CI workflows
├── docker-compose.yml             # Single file with profiles
├── render.yaml                    # Single Render blueprint
├── Makefile                       # Dev commands
└── README.md
```

## Service Boundary Definitions

### 1. Gateway (`apps/gateway/`)

**Responsibility**: HTTP entry point for the chat system. Handles all external
HTTP requests, authenticates them, applies CORS/rate-limiting, and routes to
appropriate backend services.

| Owns | Does NOT own |
|------|-------------|
| Auth + CORS + rate limiting | RAG/LLM logic |
| Request routing/proxying | Vector search |
| Scraper job orchestration (Modal triggers) | Embedding model management |
| Embedding job orchestration (Modal triggers) | Document content analysis |
| WebSocket/streaming passthrough | |
| Data management CRUD (documents, corpus) | |
| OpenAPI schema aggregation | |

**Database schema**: `gateway.*` — scraping_jobs, documents, corpus, job_status
**Calls**: Agent (HTTP), Modal SDK (scraper, embedding, reindex workers)
**Called by**: chat-frontend, data-management-frontend

### 2. Agent (`apps/agent/`)

**Responsibility**: The "brain" of the system. Runs the LlamaIndex RAG pipeline,
manages conversations, executes tool calls, performs vector search, and generates
AI responses.

| Owns | Does NOT own |
|------|-------------|
| LlamaIndex RAG pipeline | HTTP routing/auth |
| Conversation memory | Job orchestration |
| Tool calling framework | Scraping logic |
| Vector search (pgvector) | Document CRUD |
| LLM provider routing (vLLM primary) | |
| Response generation + streaming | |
| Guardrails / safety filters | |

**Database schema**: `agent.*` — conversations, vectors, tool_results, embeddings
**Calls**: vLLM (OpenAI-compatible API via LlamaIndex), PostgreSQL (pgvector)
**Called by**: Gateway (HTTP internal)

### 3. Data Management API (`apps/data-management-api/`)

**Responsibility**: CRUD service for managing the corpus of scraped documents,
metadata, and content.

| Owns | Does NOT own |
|------|-------------|
| Document CRUD operations | Scraping execution |
| Corpus management | Embedding generation |
| Metadata management | RAG retrieval |
| Content storage | |

**Database schema**: `data_mgmt.*` — documents, metadata, corpus_items
**Calls**: PostgreSQL
**Called by**: data-management-frontend, gateway

### 4. vLLM Inference (`apps/vllm-inference/`)

**Responsibility**: Run an LLM model on Modal's serverless GPU infrastructure
via vLLM, exposing an OpenAI-compatible API endpoint.

**Key integration**: LlamaIndex's `llama-index-llms-vllm` connects to this
service's OpenAI-compatible endpoint for inference.

**Runtime**: Modal serverless GPU (H100/A100)
**Protocol**: OpenAI-compatible REST API (`/v1/completions`, `/v1/chat/completions`)

### 5. Embedding Worker (`apps/embedding-worker/`)

**Responsibility**: Batch embedding of documents using LlamaIndex's embedding
pipeline on Modal GPU.

**Runtime**: Modal serverless GPU
**Protocol**: Modal function invocation (job queue)

### 6. Scraper Worker (`apps/scraper-worker/`)

**Responsibility**: Web scraping and content extraction as Modal background jobs.
No Render deployment — pure background processing.

**Runtime**: Modal serverless (CPU or GPU depending on workload)
**Protocol**: Modal function invocation (job queue)

### 7. Indexing Worker (`apps/indexing-worker/`)

**Responsibility**: Document indexing pipeline — single-doc indexing, batch
indexing of multiple pages/content, selective re-indexing of changed documents,
and full rebuild when the embedding model changes.

**Runtime**: Modal serverless (GPU for embedding)
**Protocol**: Modal function invocation, Modal Batch (spawn_map)

### 8. PgAdmin (`apps/pgadmin/`)

**Responsibility**: PostgreSQL management UI deployed as a Render private service.
Not publicly accessible — internal only.

**Runtime**: Render private service (Docker image: `dpage/pgadmin4`)

## Communication Patterns

```
chat-frontend ──HTTP──► gateway ──HTTP──► agent ──OpenAI API──► vllm-inference (Modal)
                           │                │
                           │                └──pgvector──► PostgreSQL (agent.*)
                           │
                           ├──HTTP──► data-management-api ──► PostgreSQL (data_mgmt.*)
                           │
                           ├──Modal SDK──► scraper-worker
                           ├──Modal SDK──► embedding-worker
                           └──Modal SDK──► indexing-worker

data-management-frontend ──HTTP──► data-management-api

pgadmin ──Admin──► PostgreSQL
```

## Schema-Per-Service Plan

| Schema | Owner | Tables (initial) |
|--------|-------|-----------------|
| `gateway` | gateway | scraping_jobs, job_status, api_keys, rate_limits |
| `agent` | agent | conversations, messages, vectors, tool_results, embeddings_metadata |
| `data_mgmt` | data-management-api | documents, corpus_items, metadata, sources |
| `shared` | (read-only by all) | migrations_log, feature_flags |

Each service's `DATABASE_URL` will include `?options=-c search_path=<schema>,shared,public`
to default to its own schema while allowing access to shared and public (pgvector extension).
