# Feature Specification: Modal scraper gateway persistence alignment

**Feature Branch**: `011-modal-scraper-gateway-env`  
**Created**: 2026-04-23  
**Status**: Draft  
**Input**: User description: "Please investigate this failure on the Modal scraper instance: ConfigError stating that Modal scraper workers must persist through the Render gateway (HTTP), not a direct Postgres connection from Modal; operators should set gateway base URL and shared API keys per deployment contract, may omit database URLs on Modal for pipeline-only workers when that pair is set, with an exceptional debugging-only bypass documented."

## Clarifications

### Session 2026-04-23

- Q: Should the feature’s in-scope delivery explicitly include engineering changes (worker failure handling, automated tests) alongside operator documentation, or operations-only? → A: **Full remediation** — Modal worker exception handling (no masked configuration error), expanded automated regression checks, and deployment contract / checklist updates as needed.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Restore scraper pipeline execution (Priority: P1)

An operator discovers that hosted scraper workers fail immediately when a job runs, with an explicit message that workers are not allowed to use a direct database connection from the worker runtime and must persist through the organisation’s gateway instead. The operator aligns the worker runtime configuration and the gateway’s shared ingest credentials with the single documented deployment contract so that standard scrape jobs can run again without that configuration failure.

**Why this priority**: Without this, no pipeline work completes; community ingestion and downstream RAG freshness stall.

**Independent Test**: Deploy or simulate the worker runtime with only the disallowed path (database URL present on the worker without gateway persistence pair); confirm failure. Apply contract-aligned settings; confirm a representative scrape job completes persistence steps without that error.

**Acceptance Scenarios**:

1. **Given** worker runtime is misaligned with the persistence policy, **When** a scrape job starts, **Then** the job fails fast with guidance that points operators to the documented environment contract (not an opaque connectivity error).
2. **Given** gateway base URL and shared ingest secrets match between gateway and worker runtime per contract, **When** a pipeline-only scrape job runs, **Then** the job progresses past persistence initialization without the blocking configuration error class.
3. **Given** gateway-owned job creation is in use, **When** the gateway enqueues work to the worker with a stable job identifier, **Then** the worker does not require a worker-side database URL for that enqueue path.

---

### User Story 2 - Verify parity without guesswork (Priority: P2)

An operator uses the published go/no-go checklist for hosted scraper persistence to confirm gateway flags, gateway database connectivity, worker persistence mode (database URL vs gateway HTTP ingest), and matching shared keys—so misconfiguration is found before jobs hit production volume.

**Why this priority**: Prevents repeat incidents and shortens mean time to recovery.

**Independent Test**: Walk the checklist against staging; record pass/fail per row; a deliberate single mismatch fails exactly one check with an obvious remediation.

**Acceptance Scenarios**:

1. **Given** checklist item for gateway/worker key parity, **When** keys differ by one segment, **Then** the checklist fails until both sides list the same ordered set of segments as required by contract.
2. **Given** checklist item for worker persistence mode, **When** only a disallowed combination is set, **Then** the checklist documents the required remediation (gateway HTTP pair or approved external database URL pattern per contract—not internal hostnames).

---

### User Story 3 - Controlled exception path (Priority: P3)

For exceptional debugging approved by the organisation, an operator may temporarily enable an explicit bypass that allows direct database use from the worker runtime, understanding it is unsupported for normal operation and must be reverted.

**Why this priority**: Unblocks rare deep debugging without eroding the default security and boundary posture.

**Independent Test**: With bypass enabled per contract, a narrow diagnostic job runs; with bypass disabled, the same misconfiguration fails fast again.

**Acceptance Scenarios**:

1. **Given** organisation policy allows a time-bounded bypass, **When** bypass is enabled only on the worker runtime, **Then** diagnostic jobs may proceed and all bypass usage is auditable (who/when) via change records or secret audit logs.
2. **Given** bypass is disabled, **When** workers lack gateway HTTP persistence configuration, **Then** policy enforcement behavior matches Story 1 (fail fast with contract reference).

---

### Edge Cases

- Worker runtime has a database URL that uses a hostname only reachable inside another network (e.g. internal database hostname); workers must not rely on that for pipeline-only mode when policy forbids direct access.
- Multiple key segments in the shared list: any segment may be used for ingest authorization on the gateway; worker runtime uses the first segment for the ingest header—operators rotating keys must update both sides together.
- Legacy mode still uses an externally reachable database URL on the worker runtime per contract; policy text must remain accurate for both legacy and gateway-HTTP modes.
- Gateway temporarily unreachable: worker behavior (retry vs fail) is out of scope for this spec except that misconfiguration vs transient outage must be distinguishable in operator-facing messages where already implemented.
- Generic worker failure handlers MUST NOT re-invoke persistence initialization in a way that surfaces a **second identical** configuration error after the first (operators must see one clear failure, not a chained duplicate trace).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST enforce that Modal-hosted scraper workers used for the standard pipeline do not open a direct database connection from Modal when organisation policy requires persistence via the gateway, except when an explicitly documented, operator-approved bypass flag is set for exceptional debugging.
- **FR-002**: When enforcement triggers, the worker MUST surface a configuration error that names the required remediation category (gateway public entrypoint URL plus matching shared ingest secrets aligned with the gateway, or omit worker database URLs for pipeline-only workers when that pair is set, or use the documented bypass only for exceptions).
- **FR-003**: Operators MUST be able to reconcile Modal worker secrets and gateway secrets against one authoritative deployment contract document so that key names and semantics do not drift between platforms.
- **FR-004**: For gateway-owned job submission flows, the gateway MUST be able to create the job record in its own data store and pass a stable job identifier to the worker so the worker can operate without opening a worker-side database connection for that control step, when that mode is enabled by organisation configuration.
- **FR-005**: The worker runtime MUST use the first segment of the comma-separated shared secret list for pipeline ingest authorization when using gateway HTTP persistence, and the gateway MUST accept any listed segment as defined in the deployment contract.
- **FR-006**: Observability for ingestion MUST remain sufficient for operators to correlate failed jobs with configuration class (Constitution: operational simplicity)—job or request identifiers SHOULD appear in logs or job status surfaces operators already use.
- **FR-007**: Documentation MUST state that the debugging bypass is not for production steady state and must be time-bounded and audited.
- **FR-008**: Delivery MUST include changes to Modal-hosted worker entrypoint failure handling so that a configuration error raised when persistence cannot be initialized is not obscured by a repeated configuration error during generic exception handling.
- **FR-009**: Delivery MUST include automated regression checks for the persistence-configuration matrix (including incomplete gateway HTTP pairings such as missing public entrypoint or missing shared ingest secret alignment) in the repository’s standard continuous quality pipeline for the scraper component.

### Key Entities *(include if feature involves data)*

- **Hosted worker runtime configuration**: Non-secret and secret variables that define how a scrape job persists state (direct datastore URL vs gateway base URL plus shared ingest secrets vs temporary bypass).
- **Gateway ingest authorization list**: Ordered comma-separated shared secrets mirrored on gateway and worker runtime; used to authorize pipeline ingest traffic.
- **Scrape job**: A unit of work with an identifier, status, and persistence trail; may be created on the gateway before worker execution when gateway-owned persistence is enabled.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In a validation environment that mirrors production policy, at least one representative scrape job completes without hitting the blocking “disallowed direct database from worker runtime” configuration error after remediation.
- **SC-002**: After remediation, five consecutive representative pipeline jobs in that environment do not reproduce the same configuration error class.
- **SC-003**: An operator following only the published deployment contract and checklist can complete parity verification (gateway mode, worker persistence mode, key parity) in one sitting without undocumented variables.
- **SC-004**: In a tabletop validation, three deliberately seeded misconfigurations (missing public gateway entrypoint, ingest secret mismatch between gateway and worker, worker datastore URL using an internal-only hostname while policy forbids direct access) are each mapped to the correct checklist remediation row on the first pass without ad-hoc code reading.
- **SC-005**: After delivery, the scraper component’s standard automated quality gate fails if disallowed persistence combinations for hosted workers are regressed or if the duplicate-configuration-error failure pattern is reintroduced.

## Assumptions

- Organisation hosts the gateway on Render (or equivalent) with a stable public base URL and uses Modal for scraper workers, matching the incident context.
- The deployment contract document referenced in errors is kept current when new variables are introduced; this feature prioritizes alignment and operability over changing product UX for end users.
- “Pipeline-only workers” may omit worker-side datastore URLs when gateway HTTP persistence and matching secrets are correctly set, per contract.
- Direct database from Modal remains supported only via documented external datastore URLs or the exceptional bypass, not internal-only hostnames.
- In-scope delivery includes **engineering** (worker failure paths, automated regression checks) as well as **operator-facing** contract and checklist accuracy—not configuration alignment alone.
- **FR-004** (gateway-owned job row + stable `job_id` passed into Modal submit when `MODAL_SCRAPER_PERSIST_VIA_GATEWAY` is enabled) is **already enforced** in the gateway codebase; feature **009** treats it as **verify-on-regression** via existing backend tests (e.g. `test_modal_scraper_submit_gateway_persist_injects_job_id`), not new gateway product work unless CI or staging proves otherwise.
- **FR-005** gateway clause (“accept any `SCRAPER_API_KEYS` segment for pipeline ingest”) is **already covered** by existing gateway tests (e.g. `test_pipeline_ingest_accepts_any_listed_api_key`); **009** focuses worker first-segment behavior and docs; extend gateway tests only if ingest semantics change in this effort.
