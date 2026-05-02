# Contract: Corpus Sync Boundary

## Purpose

Define non-negotiable integration boundaries that keep corpus state consistent between `apps/data-management-frontend`, `apis/data-management-api`, `backend` gateway, `frontend` documents tab, and canonical Postgres.

## Canonical Source Contract

- Production corpus source MUST be Postgres from `DATABASE_URL`.
- No production path may serve corpus data from mock, fixture-only, placeholder, or in-memory providers.
- Any detected non-canonical production source is release-blocking.

## Boundary Ownership Contract

### 1) DM Frontend <-> DM API

- Consumer: `apps/data-management-frontend`
- Provider: `apis/data-management-api`
- Allowed operations: read + write
- Verification: consumer pact + provider pact + integration tests asserting persisted DB effects.

### 2) Frontend Documents Tab <-> Gateway API

- Consumer: `frontend` documents tab
- Provider: `backend` gateway API
- Allowed operations: read-only for corpus
- Verification: consumer pact + provider pact + integration tests asserting canonical projection reads.

## Freshness Contract

- Persisted corpus writes must be visible via frontend documents tab path within 30 seconds.
- Any run exceeding 30 seconds in release validation is a failure.

## Failure Behavior Contract

- If canonical DB path or gateway path is unavailable, frontend documents tab must fail closed.
- Fail-closed means:
  - explicit outage state is shown,
  - stale or cached corpus list is not displayed as current.

## Change Synchronization Contract

- Any schema/response/route change on DM API or gateway affecting corpus must update:
  - consumer pact expectations,
  - provider verification tests,
  - related integration/system tests,
  - corresponding contract docs in this feature set.
