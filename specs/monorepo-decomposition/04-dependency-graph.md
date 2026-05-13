# 04 — Dependency Graph

> Auto-generated: 2026-05-12

See [diagrams/dependency-graph.md](./diagrams/dependency-graph.md) for visual representations.

## Service-to-Service Dependencies

| Source | Target | Protocol | Direction | Purpose |
|--------|--------|----------|-----------|---------|
| chat-frontend | gateway | HTTP REST | → | All user queries |
| data-management-frontend | data-management-api | HTTP REST | → | Document/corpus CRUD |
| gateway | agent | HTTP REST (internal) | → | RAG query delegation |
| gateway | data-management-api | HTTP REST (internal) | → | Data CRUD proxy |
| gateway | scraper-worker | Modal SDK | → | Trigger scraping jobs |
| gateway | embedding-worker | Modal SDK | → | Trigger embedding jobs |
| gateway | indexing-worker | Modal SDK | → | Trigger indexing jobs |
| agent | vllm-inference | OpenAI-compatible API | → | LLM inference |
| agent | PostgreSQL | pgvector SQL | → | Vector similarity search |
| gateway | PostgreSQL | SQL | → | Job tracking, routing data |
| data-management-api | PostgreSQL | SQL | → | Document CRUD |
| embedding-worker | PostgreSQL | SQL | → | Write vector embeddings |
| scraper-worker | PostgreSQL | SQL | → | Write scraped documents |
| pgadmin | PostgreSQL | PostgreSQL protocol | → | Admin access |

## Package Dependencies

| Package | Consumed By | Purpose |
|---------|------------|---------|
| packages/db | gateway, agent, data-management-api | DB models, migrations, connection |
| packages/config | All Python services | Env loading, validation |
| packages/common | gateway, agent, data-management-api | Types, errors, constants |

## External Dependencies

| External Service | Consumed By | Purpose |
|-----------------|------------|---------|
| Modal Runtime | vllm-inference, embedding-worker, scraper-worker, reindex-worker | Serverless GPU/CPU compute |
| Render | All web services, pgadmin, postgres | Hosting platform |
| GitHub | CI workflows | Code hosting, Actions |

## Circular Dependencies

**None identified.** All dependencies are unidirectional:
- Frontends → APIs → Workers → Database
- No service depends on a service that depends back on it
