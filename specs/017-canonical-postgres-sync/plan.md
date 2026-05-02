# Implementation Plan: Canonical Postgres Corpus Sync

**Branch**: `017-canonical-postgres-sync` | **Date**: 2026-04-29 | **Spec**: [spec.md](./spec.md)  
**Input**: Feature specification from `specs/017-canonical-postgres-sync/spec.md` with clarifications for integration ownership, pact depth, consistency SLO, fail-closed behavior, and per-suite coverage gates.

## Summary

Align corpus behavior across `apps/data-management-frontend` and `frontend` documents tab by enforcing one canonical persistence path (`DATABASE_URL` Postgres), strict write/read ownership boundaries, and synchronized contract/integration/system testing. The implementation will harden production no-mock guarantees, lock consumer/provider contracts on both API boundaries, and add measurable test gates including Playwright system-level checks and per-suite pact/contract/integration/system coverage enforcement.

## Technical Context

**Language/Version**: TypeScript 5.x (`frontend`, `apps/data-management-frontend`), Python 3.11+ (`backend`, `apis/data-management-api`).  
**Primary Dependencies**: React/Vite frontend stacks, FastAPI services, PostgreSQL drivers/ORM already used in backend services, Vitest + Pact JS, pytest + Pact Python, Playwright for end-to-end system tests.  
**Storage**: PostgreSQL via canonical `DATABASE_URL` (single source of truth for corpus state).  
**Testing**: Vitest pact tests (`frontend/tests/pact`, `apps/data-management-frontend/tests/pact`), pytest pact/contract tests (`backend/tests/pact`, `apis/data-management-api/tests/pact`, `backend/tests/contracts`), Playwright E2E/system tests, integration tests against persisted DB state, `make ci` gate.  
**Target Platform**: Render-hosted production services and web frontends, Linux CI runners.  
**Project Type**: Multi-service monorepo with two frontends and multiple HTTP APIs.  
**Performance Goals**: Enforce corpus write-to-visibility divergence <=30s for release candidates; no regression in existing user-facing corpus load paths.  
**Constraints**: No mocks/placeholders in production paths; frontend documents tab is read-only; data-management frontend owns writes via DM API; fail-closed outage behavior; per-suite test gating required; release-blocking conditions include SLO breaches, contract-drift failures, or missing impacted suites.  
**Scale/Scope**: Corpus synchronization behavior across DM frontend, DM API, gateway API, frontend documents tab, and canonical DB, including CI contract/test orchestration changes.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| Community benefit | Pass | Reliable corpus parity reduces misinformation risk for community-facing retrieval surfaces. |
| Trustworthy retrieval | Pass | Canonical DB flow + fail-closed state prevents stale/unverifiable corpus display. |
| Data stewardship | Pass | Single production source and no-placeholder policy improve auditability and reduce accidental data leakage paths. |
| Safety & quality | Pass | Adds stronger pact/contract/integration/system gates and suite-specific coverage requirements. |
| Service boundaries | Pass | Explicitly contracts DM frontend↔DM API and frontend↔gateway boundaries with synchronized provider/consumer verification. |

**Post–Phase 1 re-check**: Generated artifacts in `contracts/` define boundary-level test and ownership contracts. `data-model.md` and `quickstart.md` preserve canonical DB and production-path constraints without weakening service boundaries.

## Project Structure

### Documentation (this feature)

```text
specs/017-canonical-postgres-sync/
├── README.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── corpus-sync-boundary-contract.md
│   └── testing-gates-matrix.md
├── artifacts/
│   ├── final-validation-notes.md
│   └── ci-evidence.md
├── checklists/
│   ├── requirements.md
│   └── plan-consistency.md
└── tasks.md
```

### Source code (expected touchpoints)

```text
apps/data-management-frontend/
├── src/                         # corpus management UI + API clients
└── tests/
    ├── pact/
    ├── integration/
    └── e2e/

apis/data-management-api/
├── apps/backend/vecinita_dm_api/routers/
└── tests/
    ├── pact/
    ├── contracts/
    └── integration/

backend/
├── src/api/                     # gateway endpoints used by frontend documents tab
└── tests/
    ├── pact/
    ├── contracts/
    └── integration/

frontend/
├── src/                         # documents tab read path
└── tests/
    ├── pact/
    ├── integration/
    └── e2e/                     # Playwright/system-level flows

.cursor/hooks/registry-contract-pact-tests.json
TESTING_DOCUMENTATION.md
Makefile
```

**Structure Decision**: Keep implementation within existing service/frontend boundaries; no new service introduced. Cross-boundary guarantees are handled via contract artifacts and test pipeline gates, not runtime coupling.

## Complexity Tracking

No constitution violations requiring explicit exception.

## Phase 0: Research

- Resolve test-layer responsibilities across pact/contract/integration/system tests.
- Define production-safe no-mock enforcement strategy that still allows isolated pact testing where appropriate.
- Determine best path for Playwright system assertions using controlled seeded data and deterministic visibility checks.
- Define requirement-level recovery and concurrency semantics for partial failure and near-simultaneous updates.

Results recorded in [research.md](./research.md).

## Phase 1: Design & Contracts

- [data-model.md](./data-model.md): canonical entities and sync invariants across services.
- [contracts/corpus-sync-boundary-contract.md](./contracts/corpus-sync-boundary-contract.md): write/read ownership + DB source contract.
- [contracts/testing-gates-matrix.md](./contracts/testing-gates-matrix.md): pact/contract/integration/system gate definitions and coverage thresholds.
- [quickstart.md](./quickstart.md): developer workflow for validating canonical sync and test gates.

## Next Step

Run `/speckit.tasks` to generate execution-ready tasks from this plan, then implement with `/speckit-implement`.
