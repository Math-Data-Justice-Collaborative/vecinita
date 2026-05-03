# Research: Canonical Postgres Corpus Sync

Phase 0 decisions for feature `017-canonical-postgres-sync`.

## Decision 1 - Canonical data ownership model

**Decision**: Use `DATABASE_URL` Postgres as the only canonical persistence for corpus state. `apps/data-management-frontend` can mutate corpus only via data-management API. `frontend` documents tab reads only through gateway API and performs no corpus writes.

**Rationale**: This directly resolves current drift by removing multi-writer ambiguity and enforcing one DB-backed source of truth.

**Alternatives considered**:
- Dual write paths from both frontends: rejected due to race/conflict risk and harder contract verification.
- Gateway-owned writes for all callers: rejected because it inverts existing DM operational ownership with unnecessary migration scope.

## Decision 2 - Pact and contract scope across boundaries

**Decision**: Enforce bidirectional consumer-provider verification for both boundaries:
1. DM frontend <-> DM API
2. Frontend documents tab <-> Gateway API

Provider verification runs against real provider routes with controlled deterministic state setup. Contract tests are complemented by integration tests that assert persisted Postgres effects.

**Rationale**: Pact catches request/response drift early, but persistence semantics must still be validated with integration tests against real DB effects.

**Alternatives considered**:
- Provider-only pact verification: rejected; misses consumer expectation drift.
- End-to-end-only testing: rejected; too broad to isolate contract mismatches quickly.

## Decision 3 - Production no-mock policy and test layering

**Decision**: Keep mocks isolated to consumer-side pact tests only. Production profile, integration tests, and system tests must run with real service paths and canonical DB (no placeholders/in-memory substitutes in production deployment paths).

**Rationale**: This preserves pact isolation benefits while honoring strict production requirements.

**Alternatives considered**:
- Ban all mocks in all test layers: rejected; would reduce contract-test speed and precision.
- Allow placeholders in production fallback: rejected by spec fail-closed requirement.

## Decision 4 - System-level verification with Playwright

**Decision**: Add/extend Playwright journeys that:
- seed deterministic corpus state through approved write path,
- validate documents tab read-only behavior,
- assert end-to-end visibility within <=30 seconds,
- assert fail-closed outage UX behavior.

**Rationale**: System tests validate real user-visible behavior spanning frontend, gateway, API, and DB boundaries.

**Alternatives considered**:
- API-only system checks: rejected because UI outage and read-only constraints are user-facing and must be validated at the browser layer.

## Decision 5 - Coverage and CI gating policy

**Decision**: Define per-suite required gates for pact, contract, integration, and system tests. CI must run impacted suites by change scope and fail merge when a required suite is skipped or below threshold.

**Rationale**: A single aggregate coverage metric can hide missing protection in one critical test layer.

**Alternatives considered**:
- Pass/fail-only without per-suite requirements: rejected; insufficient for this cross-boundary risk profile.
