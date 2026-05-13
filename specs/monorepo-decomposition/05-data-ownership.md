# 05 — Data Ownership

> Auto-generated: 2026-05-12

See also: [diagrams/data-ownership.md](./diagrams/data-ownership.md)

## Database: PostgreSQL 16 (Render)

Single instance with schema-per-service logical separation (TD-002).

### Schema Ownership

| Schema | Owner Service | Read Access | Write Access |
|--------|-------------|-------------|--------------|
| `gateway` | gateway | gateway | gateway |
| `agent` | agent | agent, gateway (read-only) | agent, embedding-worker |
| `data_mgmt` | data-management-api | data-management-api, gateway | data-management-api, scraper-worker |
| `shared` | (all) | All services | Migration scripts only |
| `public` | (system) | All services | pgvector extension objects |

### Table Ownership (Proposed)

#### gateway schema
| Table | Purpose | Writers | Readers |
|-------|---------|---------|---------|
| `gateway.scraping_jobs` | Track scraping job status | gateway | gateway, data-management-frontend (via API) |
| `gateway.job_status` | Generic async job tracking | gateway | gateway |
| `gateway.api_keys` | API authentication keys | gateway | gateway |
| `gateway.rate_limits` | Rate limiting state | gateway | gateway |

#### agent schema
| Table | Purpose | Writers | Readers |
|-------|---------|---------|---------|
| `agent.conversations` | Chat conversation history | agent | agent |
| `agent.messages` | Individual messages in conversations | agent | agent |
| `agent.vectors` | pgvector embeddings for RAG | embedding-worker, agent | agent |
| `agent.tool_results` | Cached tool call results | agent | agent |
| `agent.embeddings_metadata` | Metadata about embedding batches | embedding-worker | agent, gateway |

#### data_mgmt schema
| Table | Purpose | Writers | Readers |
|-------|---------|---------|---------|
| `data_mgmt.documents` | Scraped/uploaded document content | scraper-worker, data-management-api | data-management-api, gateway, agent |
| `data_mgmt.corpus_items` | Corpus membership (which docs in which corpus) | data-management-api | data-management-api, agent |
| `data_mgmt.metadata` | Document metadata (source, date, tags) | scraper-worker, data-management-api | data-management-api |
| `data_mgmt.sources` | Scraping source definitions | data-management-api | gateway, scraper-worker |

#### shared schema
| Table | Purpose | Writers | Readers |
|-------|---------|---------|---------|
| `shared.migrations_log` | Track applied migrations | Migration scripts | All services |
| `shared.feature_flags` | Runtime feature toggles | Admin/migration | All services |

### Cross-Schema Access Patterns

| Access Pattern | Risk | Mitigation |
|---------------|------|------------|
| Agent reads `data_mgmt.documents` for RAG context | Read-only, low risk | Use read-only views or explicit cross-schema queries |
| Embedding-worker writes to `agent.vectors` | Write access across ownership | Acceptable — embedding-worker is a "producer" for agent's vector index |
| Scraper-worker writes to `data_mgmt.documents` | Write access across ownership | Acceptable — scraper is a "producer" for data-management's document store |
| Gateway reads `agent.embeddings_metadata` | Read-only, low risk | Use read-only view |

### pgvector Extension

The `vector` extension lives in the `public` schema (PostgreSQL requirement
for extensions). All services can use `public.vector` type. The actual vector
data lives in `agent.vectors` table.

```sql
CREATE EXTENSION IF NOT EXISTS vector SCHEMA public;

CREATE TABLE agent.vectors (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES data_mgmt.documents(id),
    embedding vector(384),
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```
