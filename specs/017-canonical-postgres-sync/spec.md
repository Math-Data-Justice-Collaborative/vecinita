# Feature Specification: Canonical Postgres Corpus Sync

**Feature Branch**: `017-canonical-postgres-sync`  
**Created**: 2026-04-29  
**Status**: Draft  
**Input**: User description: "There is currently a discrepancy between apps/data-management-frontend and the frontend documents tab. Both must be connected to DATABASE_URL Postgres as the canonical database source, with no mocks/placeholders for production, plus pact/contract/system/integration test coverage across data management frontend/API/database and gateway/frontend documents tab."

## Clarifications

### Session 2026-04-29

- Q: Which integration boundary owns corpus write operations? → A: `apps/data-management-frontend` writes corpus only via data management API; `frontend` documents tab is read-only via gateway API.
- Q: What verification depth is required across integration boundaries? → A: Bidirectional consumer-provider pact verification for both boundaries, plus integration tests on persisted DB effects.
- Q: What consistency window is required between persisted corpus writes and frontend documents visibility? → A: Near-real-time consistency with a strict maximum 30-second divergence window; failures block release.
- Q: How should frontend documents behave during canonical DB or gateway outages? → A: Fail closed; show explicit outage state and block stale corpus display.
- Q: How should test coverage gates be enforced across test types? → A: Enforce per-suite minimums (pact, contract, integration, system) and require impacted suites to run for relevant code changes.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Canonical corpus parity across experiences (Priority: P1)

As an operator using both the data management interface and the main frontend documents tab, I need both surfaces to show the same corpus state so I can trust what users see and what admins manage.

**Why this priority**: Corpus inconsistency in production creates immediate trust and operational risk.

**Independent Test**: Seed a known corpus dataset in the canonical database, then verify both experiences show the same document set, statuses, and counts without manual reconciliation.

**Acceptance Scenarios**:

1. **Given** documents exist in the canonical production database, **When** the operator loads the data management corpus view and the frontend documents tab, **Then** both views show the same document membership and state.
2. **Given** a document is added, updated, or removed through the approved data flow, **When** each interface refreshes, **Then** both reflect the same change from the same source of truth.
3. **Given** a user is in the frontend documents tab, **When** they interact with corpus content, **Then** no write operation is issued and only gateway-backed reads are allowed.

---

### User Story 2 - Production behavior without mocks or placeholders (Priority: P1)

As a release owner, I need production deployments to reject mock or placeholder data sources so live users only interact with real persisted corpus data.

**Why this priority**: Mock data in production can expose incorrect content and break data governance.

**Independent Test**: Execute a production-profile deployment validation that fails if any configured data path resolves to mock or placeholder providers.

**Acceptance Scenarios**:

1. **Given** a production deployment candidate, **When** environment and runtime checks are executed, **Then** the deployment is marked failed if any mock or placeholder corpus source is configured or reachable.
2. **Given** a valid production configuration, **When** the system starts and serves corpus views, **Then** all corpus reads and writes flow through the canonical production database connection.
3. **Given** the canonical DB path or gateway path is unavailable, **When** a user opens the frontend documents tab, **Then** the UI shows an explicit outage state and no stale corpus list is displayed.

---

### User Story 3 - Contract confidence across system boundaries (Priority: P2)

As an engineer maintaining multiple services and clients, I need automated contract and integration verification so schema or behavior drift is caught before release.

**Why this priority**: Multiple boundaries (frontend, gateway, data management API, database) increase drift risk without explicit contract checks.

**Independent Test**: Run pact, contract, integration, and system-level suites that verify request/response behavior and persisted state consistency for the corpus flow end to end.

**Acceptance Scenarios**:

1. **Given** a change to corpus-facing interfaces, **When** contract and pact suites run, **Then** mismatched payloads, fields, or status behavior are flagged before merge.
2. **Given** a release candidate, **When** integration and system-level tests run against real persistence, **Then** they verify the same corpus behavior across data management and frontend documents tab journeys.

---

### Edge Cases

- What happens when one interface shows a recently changed corpus item while the other reads stale data due to delayed refresh?
- How does the system handle canonical database connection failures while preventing fallback to placeholder data?
- What happens when contract-compatible requests return semantically inconsistent corpus states across service boundaries?
- How is partial failure handled when one service updates corpus state but an upstream or downstream boundary fails?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST use the `DATABASE_URL`-targeted production PostgreSQL database as the single canonical source of corpus truth for both the data management frontend and the frontend documents tab experience.
- **FR-002**: The corpus data shown in the data management frontend and frontend documents tab MUST remain synchronized such that both surfaces resolve to the same canonical document state for equivalent queries.
- **FR-002a**: Corpus write operations MUST be owned only by `apps/data-management-frontend` through the data management API.
- **FR-002b**: The frontend documents tab MUST be read-only for corpus operations and MUST consume corpus data only through the gateway API.
- **FR-003**: Production deployments MUST reject mock, fixture, placeholder, or in-memory corpus data providers for all paths used by the two user-facing corpus experiences.
- **FR-003a**: When canonical data dependencies are unavailable, the frontend documents tab MUST fail closed and MUST NOT display cached or stale corpus records.
- **FR-004**: The data management API corpus contract with its frontend consumer MUST be enforced through automated pact and contract tests that run in CI.
- **FR-005**: The gateway API contract with the frontend documents tab consumer MUST be enforced through automated pact and contract tests that run in CI.
- **FR-005a**: For both boundaries, contract verification MUST include both consumer-side and provider-side pact validation in CI.
- **FR-006**: Automated integration tests MUST verify corpus read/write propagation from data management workflows through persisted storage and into frontend document retrieval flows.
- **FR-006a**: Integration tests MUST assert persisted PostgreSQL state changes (create, update, delete, visibility) and confirm those persisted effects are reflected through gateway reads.
- **FR-006b**: The maximum allowed divergence window between a persisted corpus write and its visibility in the frontend documents tab MUST be 30 seconds.
- **FR-006c**: Release validation MUST fail when integration or system tests show divergence beyond the 30-second limit.
- **FR-006d**: The system MUST define and validate recovery behavior for partial cross-service failures (write succeeds but projection/read path fails), including explicit retry or reconciliation requirements and test coverage.
- **FR-006e**: The system MUST define concurrency handling for near-simultaneous corpus updates, including deterministic conflict resolution semantics and visibility expectations.
- **FR-007**: Automated system-level tests MUST verify end-to-end corpus consistency across the data management frontend, data management API, canonical database, gateway API, and frontend documents tab.
- **FR-008**: Test coverage reporting MUST include pact, contract, integration, and system-level suites for this feature and MUST fail release gating when required suites are missing or failing.
- **FR-008a**: Coverage policy MUST define and enforce minimum thresholds separately for pact, contract, integration, and system-level suites rather than only a single combined threshold; required minimums are pact >= 95%, contract >= 95%, integration >= 90%, and system >= 85%, measured as line coverage by each suite's primary CI coverage reporter.
- **FR-008b**: CI change-impact rules MUST require all impacted suites to execute for relevant code or contract changes before merge approval.
- **FR-009**: Any schema or contract changes affecting corpus retrieval, mutation, or display MUST update all dependent contract artifacts and tests in the same change set, and CI MUST enforce this via a contract-drift validation step.

### Key Entities *(include if feature involves data)*

- **Corpus Document**: A persisted knowledge unit that includes identity, source metadata, lifecycle status, and display-ready attributes shared across interfaces.
- **Canonical Corpus View**: The normalized representation of corpus state returned to user interfaces for listing, filtering, and detail rendering.
- **Contract Boundary**: A defined request/response interaction between consumers and providers (data management frontend <> data management API; frontend documents tab <> gateway API).
- **Environment Configuration**: Deployment configuration that determines the canonical database target and enforces production-only data source policies.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In release validation runs, 100% of corpus parity checks in a deterministic sample set of at least 30 documents per candidate release show identical document identity and status results between the data management frontend corpus view and frontend documents tab for equivalent filters.
- **SC-002**: 100% of production-profile deployment validations fail when any mock or placeholder corpus source is configured, and 100% pass when only canonical-source configuration is present.
- **SC-003**: Required pact and contract suites for both service boundaries pass at least 99% of CI runs over a rolling 30-day window, with any failure blocking release; the rolling-window metric MUST be computed from the repository CI provider build history used by release approvals and published in release evidence artifacts.
- **SC-004**: End-to-end integration and system tests for corpus synchronization pass for every release candidate before deployment approval, including a measured maximum write-to-visibility lag of 30 seconds.

## Assumptions

- Existing user authentication and authorization behavior for both frontends remains unchanged by this feature.
- Only corpus-related data alignment and verification are in scope; unrelated UI behavior and non-corpus domains are out of scope.
- Equivalent queries between interfaces are defined by existing product filtering semantics and documented test fixtures.
- The canonical production database connection is already provisioned and available to deployment environments via `DATABASE_URL`.
