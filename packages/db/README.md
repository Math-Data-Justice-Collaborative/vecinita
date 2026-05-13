# `packages/db/`

Shared database session, migration helpers, and schema management used by multiple APIs.

## Schema-Per-Service Layout (Spec 023)

The database uses a schema-per-service model. Each backend service owns its tables in a dedicated PostgreSQL schema, with cross-schema grants for documented access patterns.

| Schema      | Owner Service          | Tables                                                                  |
|-------------|------------------------|-------------------------------------------------------------------------|
| `gateway`   | Gateway API            | `scraping_jobs`, `job_status`, `api_keys`, `rate_limits`                |
| `agent`     | Agent Service          | `conversations`, `messages`, `vectors`, `tool_results`, `embeddings_metadata`, `document_embeddings` |
| `data_mgmt` | Data Management API    | `documents`, `corpus_items`, `metadata`, `sources`                      |
| `shared`    | All services (read)    | `migrations_log`, `feature_flags`                                       |
| `public`    | System                 | pgvector extension objects only                                         |

### Cross-Schema Access

- Agent reads `data_mgmt.documents` (RAG context retrieval)
- Embedding-worker writes to `agent.vectors` and `agent.embeddings_metadata`
- Scraper-worker writes to `data_mgmt.documents`
- All services can read `shared.*`

### Connection Configuration

Each service sets its `search_path` via `DATABASE_URL`:

| Service              | search_path                     |
|----------------------|---------------------------------|
| Gateway              | `gateway,shared,public`         |
| Agent                | `agent,shared,public`           |
| Data Management API  | `data_mgmt,shared,public`       |

Format: `postgresql://...?options=-c search_path=<schema>,shared,public`

## Migrations

Migration scripts live in `migrations/`. Run against the shared PostgreSQL instance.

### 001 — Schema-Per-Service

**Forward migration:**

```bash
psql $DATABASE_URL -f packages/db/migrations/001_schema_per_service.sql
```

**Rollback:**

```bash
psql $DATABASE_URL -f packages/db/migrations/001_schema_per_service_rollback.sql
```

The forward migration is wrapped in a transaction and is idempotent (`CREATE SCHEMA IF NOT EXISTS`, `ALTER TABLE IF EXISTS`). The rollback moves all tables back to `public` and drops the service schemas.

## References

- [Spec 023 — Schema-Per-Service Migration](../../specs/023-schema-per-service-migration/spec.md)
- [Monorepo Layout Contract](../../specs/018-strict-monorepo-layout/contracts/monorepo-layout-boundary.md)
