# Data Model: Canonical Corpus Sync

## Entity: Corpus Document

Represents a persisted corpus record in canonical Postgres.

| Field | Description | Constraint |
|-------|-------------|------------|
| document_id | Stable document identifier | Unique, non-null |
| source_uri | Origin reference for corpus item | Non-null |
| status | Lifecycle status (active, processing, archived, failed) | Controlled enum |
| updated_at | Last canonical mutation timestamp | Non-null, monotonic per update |
| visibility_version | Monotonic read visibility marker exposed through APIs | Must reflect canonical state |

## Entity: Canonical Corpus Projection

Normalized response shape returned to UI consumers for list/detail rendering.

| Field | Description |
|-------|-------------|
| document_id | Joins to canonical document |
| display_fields | User-facing metadata fields |
| status | Current status from canonical source |
| last_synced_at | Timestamp of projection generation |

## Entity: Boundary Contract

Captures request/response guarantees for each integration boundary.

| Boundary | Consumer | Provider | Write Allowed |
|----------|----------|----------|---------------|
| dm_front_to_dm_api | `apps/data-management-frontend` | `apis/data-management-api` | Yes |
| frontend_to_gateway | `frontend` documents tab | `backend` gateway API | No |

## Entity: Test Gate Policy

Defines suite-level requirements for merge readiness.

| Suite | Purpose | Required on Impact |
|-------|---------|--------------------|
| pact | Request/response consumer-provider compatibility | Yes |
| contract | Provider behavior/schema invariants | Yes |
| integration | Persistence semantics and propagation | Yes |
| system | End-to-end user journeys and outage behavior | Yes |

## Relationships

- Corpus document mutations occur only via `dm_front_to_dm_api` boundary and persist to canonical Postgres.
- Gateway responses used by frontend documents tab derive from canonical projection and must never bypass canonical DB source.
- Test gate policy validates every boundary and persistence relationship before merge/release.

## Invariants

- Canonical source invariant: all corpus reads/writes in production trace to `DATABASE_URL` Postgres.
- Read-only UI invariant: frontend documents tab cannot issue corpus write operations.
- Freshness invariant: max write-to-visibility lag is 30 seconds in release validation.
- Outage invariant: on canonical path failure, frontend documents tab fails closed with explicit outage state and no stale corpus rendering.
