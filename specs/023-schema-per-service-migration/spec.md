# Feature Specification: Schema-Per-Service Migration

**Spec ID**: 023  
**Feature Branch**: `023-schema-per-service-migration`  
**Created**: 2026-05-13  
**Status**: Draft  
**Phase**: 4 (Migration Sequence — see `specs/monorepo-decomposition/09-migration-sequence.md`)  
**Technical Decision**: TD-002 (Schema-per-service logical separation)

## Overview

Migrate the single-schema PostgreSQL database to a schema-per-service model, creating logical
boundaries between gateway, agent, and data-management-api within the existing Render PostgreSQL 16
instance. Each service gets its own schema, its own `search_path`, and explicit cross-schema access
grants where needed.

This provides data ownership boundaries without the operational cost of multiple database instances,
while preserving a natural upgrade path to full isolation if needed later.

## Dependencies

| Spec | Title | Relationship |
|------|-------|-------------|
| 020 | Monorepo Layout | Must complete first — services must be in `apps/` structure |
| 021 | Service Extraction | Must complete first — gateway/agent must be separate services |

## Requirements

### Functional Requirements

- **FR-001**: The system MUST create PostgreSQL schemas: `gateway`, `agent`, `data_mgmt`, and
  `shared` within the existing Render PostgreSQL 16 instance.

- **FR-002**: The system MUST provide a migration script that moves existing tables from the
  `public` schema into their appropriate service-owned schemas, preserving all data, indexes,
  constraints, and sequences.

- **FR-003**: The `gateway` schema MUST own the following tables: `scraping_jobs`, `job_status`,
  `api_keys`, `rate_limits`.

- **FR-004**: The `agent` schema MUST own the following tables: `conversations`, `messages`,
  `vectors` (pgvector), `tool_results`, `embeddings_metadata`.

- **FR-005**: The `data_mgmt` schema MUST own the following tables: `documents`, `corpus_items`,
  `metadata`, `sources`.

- **FR-006**: The `shared` schema MUST own the following tables: `migrations_log`, `feature_flags`.

- **FR-007**: The `pgvector` extension MUST remain installed in the `public` schema. All services
  MUST be able to use the `vector` type from `public` regardless of their `search_path`.

- **FR-008**: Each service's `DATABASE_URL` MUST include a `search_path` option scoping it to its
  own schema, the `shared` schema, and `public`. Format:
  `?options=-c search_path=<service_schema>,shared,public`
  - Gateway: `search_path=gateway,shared,public`
  - Agent: `search_path=agent,shared,public`
  - Data Management API: `search_path=data_mgmt,shared,public`

- **FR-009**: Cross-schema access MUST be granted for the following patterns:
  - Agent service reads `data_mgmt.documents` (for RAG context retrieval)
  - Embedding-worker writes to `agent.vectors` (producer for agent's vector index)
  - Scraper-worker writes to `data_mgmt.documents` (producer for data store)
  - Gateway reads `agent.embeddings_metadata` (read-only monitoring)

- **FR-010**: The migration MUST be wrapped in a transaction and MUST be fully reversible via a
  corresponding rollback script that moves tables back to `public` schema.

- **FR-011**: All services MUST pass their health check endpoints after the migration completes
  without any code changes beyond `DATABASE_URL` configuration.

### Non-Functional Requirements

- **NFR-001**: The migration MUST complete within a single maintenance window (< 5 minutes of
  downtime for a database with < 1GB of data).
- **NFR-002**: The migration script MUST be idempotent — running it twice produces no errors and no
  data loss.
- **NFR-003**: Cross-schema grants MUST follow least-privilege: read-only where only reads are
  needed, write access only for documented producer patterns.

## User Stories

### US-001: Database administrator runs schema migration (Priority: P1)

A database administrator (or solo developer acting as one) runs the schema migration against the
production database to establish service ownership boundaries.

**Acceptance Scenarios**:

- **AS-001**: Given a PostgreSQL 16 database with all tables in `public` schema, when the migration
  script is executed, then four new schemas (`gateway`, `agent`, `data_mgmt`, `shared`) exist and
  all designated tables reside in their respective schemas.
- **AS-002**: Given the migration has been applied, when a `SELECT * FROM information_schema.tables
  WHERE table_schema = 'gateway'` is run, then it returns exactly: `scraping_jobs`, `job_status`,
  `api_keys`, `rate_limits`.
- **AS-003**: Given the migration has been applied, when a `SELECT * FROM information_schema.tables
  WHERE table_schema = 'public'` is run, then only system tables and the pgvector extension objects
  remain (no application tables).

### US-002: Gateway service operates within its schema (Priority: P1)

The gateway service connects with its scoped `DATABASE_URL` and performs all operations without
qualifying table names with schema prefixes in application code.

**Acceptance Scenarios**:

- **AS-004**: Given the gateway's `DATABASE_URL` includes `search_path=gateway,shared,public`, when
  the gateway executes `SELECT * FROM scraping_jobs`, then it resolves to `gateway.scraping_jobs`
  without error.
- **AS-005**: Given the gateway's scoped connection, when it attempts `INSERT INTO conversations
  (...)`, then the query fails with a "relation does not exist" error (enforcing boundary).
- **AS-006**: Given the gateway's scoped connection, when it reads `SELECT * FROM feature_flags`,
  then it resolves to `shared.feature_flags` successfully.

### US-003: Agent service reads cross-schema data for RAG (Priority: P1)

The agent service needs read access to `data_mgmt.documents` for RAG context retrieval while
maintaining ownership of its own schema.

**Acceptance Scenarios**:

- **AS-007**: Given the agent's scoped connection and explicit cross-schema grant, when the agent
  executes `SELECT * FROM data_mgmt.documents WHERE id = $1`, then it returns the document content
  successfully.
- **AS-008**: Given the agent's scoped connection, when it attempts `DELETE FROM
  data_mgmt.documents`, then the query fails with a permission error (read-only access).
- **AS-009**: Given the agent's scoped connection, when it executes `INSERT INTO vectors (...)`,
  then it resolves to `agent.vectors` and succeeds.

### US-004: Embedding worker writes vectors cross-schema (Priority: P1)

The embedding worker produces vector embeddings and writes them to the agent's vectors table as an
authorized cross-schema producer.

**Acceptance Scenarios**:

- **AS-010**: Given the embedding worker's connection with write grant on `agent.vectors`, when it
  inserts a new embedding row, then the row appears in `agent.vectors` with correct data.
- **AS-011**: Given the embedding worker's connection, when it attempts to read `agent.conversations`,
  then the query fails with a permission error (write access limited to `agent.vectors` and
  `agent.embeddings_metadata` only).

### US-005: Developer rolls back the migration (Priority: P2)

After the migration is applied, a developer discovers an issue and needs to revert to the original
single-schema layout.

**Acceptance Scenarios**:

- **AS-012**: Given a database with the schema migration applied, when the rollback script is
  executed, then all tables return to the `public` schema with data intact.
- **AS-013**: Given the rollback has completed, when services connect with their original
  `DATABASE_URL` (no `search_path` option), then all services pass health checks.

### US-006: Migration handles pgvector correctly (Priority: P1)

The pgvector extension and its types must remain accessible from all schemas after migration.

**Acceptance Scenarios**:

- **AS-014**: Given the migration has been applied, when `SELECT extname, extnamespace::regnamespace
  FROM pg_extension WHERE extname = 'vector'` is run, then it returns `public`.
- **AS-015**: Given a table in `agent` schema with a `vector(384)` column, when the agent inserts a
  new row with an embedding, then the insert succeeds without "type not found" errors.

## Success Criteria

- **SC-001**: After migration, `\dn` in psql shows exactly four new schemas: `gateway`, `agent`,
  `data_mgmt`, `shared` (in addition to `public`).
- **SC-002**: Zero application tables remain in the `public` schema after migration (only extension
  objects).
- **SC-003**: All three backend services (gateway, agent, data-management-api) pass their `/health`
  endpoint with HTTP 200 after migration, using only `DATABASE_URL` changes (no application code
  changes to SQL queries).
- **SC-004**: The rollback script restores the database to pre-migration state in under 60 seconds
  for databases under 1GB.
- **SC-005**: Cross-schema access tests pass: agent can read `data_mgmt.documents`, embedding-worker
  can write `agent.vectors`, scraper-worker can write `data_mgmt.documents`.
- **SC-006**: Cross-schema boundary tests pass: gateway cannot write to `agent.*`, agent cannot
  write to `data_mgmt.*`, no service can write to `shared.*` directly.
- **SC-007**: pgvector operations (insert embedding, similarity search) work correctly from the
  `agent` schema after migration.

## Implementation Notes

### Migration Script Structure

```sql
BEGIN;
-- Create schemas
CREATE SCHEMA IF NOT EXISTS gateway;
CREATE SCHEMA IF NOT EXISTS agent;
CREATE SCHEMA IF NOT EXISTS data_mgmt;
CREATE SCHEMA IF NOT EXISTS shared;

-- Move tables (example)
ALTER TABLE public.scraping_jobs SET SCHEMA gateway;
ALTER TABLE public.conversations SET SCHEMA agent;
ALTER TABLE public.documents SET SCHEMA data_mgmt;
ALTER TABLE public.migrations_log SET SCHEMA shared;

-- Grant cross-schema access
GRANT USAGE ON SCHEMA data_mgmt TO agent_role;
GRANT SELECT ON data_mgmt.documents TO agent_role;
-- ... etc
COMMIT;
```

### Rollback Script Structure

```sql
BEGIN;
ALTER TABLE gateway.scraping_jobs SET SCHEMA public;
-- ... move all tables back
DROP SCHEMA gateway;
DROP SCHEMA agent;
DROP SCHEMA data_mgmt;
DROP SCHEMA shared;
COMMIT;
```

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|-----------|
| ORM/query builder hardcodes `public` schema | Queries fail after migration | Audit all SQL and ORM config for schema assumptions before migration |
| Foreign keys across schemas break during `ALTER TABLE SET SCHEMA` | Migration fails mid-way | Order table moves to respect FK dependencies; wrap in transaction |
| Sequences not moved with tables | Auto-increment breaks | Explicitly move sequences with `ALTER SEQUENCE ... SET SCHEMA` |
| Alembic/migration tooling assumes single schema | Future migrations break | Configure migration tool with `include_schemas` / multi-schema support |

## Open Questions

- Will Render's managed PostgreSQL allow `CREATE SCHEMA` without superuser? (Most managed providers
  allow this for the database owner role.)
- Should cross-schema views be created for read-only access patterns, or should services use
  explicit fully-qualified queries?
