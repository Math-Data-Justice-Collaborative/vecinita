# Feature Specification: Consolidate scraper and stabilize job APIs

**Feature Branch**: `003-consolidate-scraper-dm`  
**Created**: 2026-04-19  
**Status**: Partial (2026-04-19) — OpenAPI alignment **T037** and nested submodule removal **SC-003**/**T027** are landed; release-blocking live gates (**SC-001**, **SC-004**, **SC-005**, **T014**, **T016**, **T034**, **FR-006** live proof) remain. Single source of truth: [baseline-notes-schemathesis.md](./baseline-notes-schemathesis.md#t041-spec-rollout-status).  
**Input**: User description: "Investigate Schemathesis failures (modal scraper job endpoints returning server errors tied to persistence connectivity; ask endpoint timing out). Address errors so the API behaves as documented. Reduce repository complexity by removing redundant duplicate `vecinita_scraper` implementations (standalone scraper service vs copy under data-management-api) and eliminating nested/embedded copies of embedding, model, and scraper capabilities inside data-management-api in favor of a single source of truth per capability."

## Clarifications

### Session 2026-04-19

- Q: After embedded copies under data-management-api are removed, what should be the primary way that application obtains scraper, embedding, and model behavior? → A: **B — Remote APIs only** — data-management-api calls separately deployed scraper, embedding, and model services over documented HTTP (or equivalent remote contract), not in-process shared packages or vendored source trees for those capabilities.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Scraping jobs work end-to-end (Priority: P1)

An operator or integrated client uses the public API to start a hosted scraping job, monitor it, and cancel it if needed. They expect predictable outcomes: jobs are accepted, visible in listings, show coherent status, and can be cancelled—without unexplained server errors when the deployment is meant to be fully operational.

**Why this priority**: Broken job lifecycle blocks ingestion and downstream community RAG value; failures surfaced as generic server errors erode trust and block automated contract verification.

**Independent Test**: In a production-like environment with persistence and job orchestration enabled, exercise create → list → get → cancel (and failure paths with invalid IDs) and confirm no undocumented 5xx responses for healthy configuration.

**Acceptance Scenarios**:

1. **Given** a correctly configured deployment, **When** a client creates a scraping job with valid inputs, **Then** the API responds with a success outcome defined by the contract (not a server error) and the job becomes discoverable.
2. **Given** at least one job exists, **When** a client lists jobs, **Then** the response reflects current jobs without a server error.
3. **Given** a known job identifier, **When** a client fetches status or requests cancellation, **Then** the API returns a contract-appropriate outcome (including explicit not-found when applicable) rather than an internal failure message.

---

### User Story 2 - One clear home for scraper capability (Priority: P2)

A maintainer clones the repository and needs to change scraping behavior once, run tests once, and ship one artifact—without reconciling two parallel packages that drift over time.

**Why this priority**: Duplicate implementations increase defect rate, slow onboarding, and violate operational simplicity; consolidation reduces long-term cost and aligns with clear service boundaries.

**Independent Test**: Repository audit shows a single authoritative scraper package path for application logic in the monorepo; data-management-api consumes scraping only through its **documented remote service contract** to that deployable, with no vendored duplicate source tree.

**Acceptance Scenarios**:

1. **Given** the monorepo after the change, **When** a maintainer searches for scraper source edits, **Then** there is one primary implementation location documented in contributor guidance.
2. **Given** a scraper change, **When** tests run for affected surfaces, **Then** there is no second copy requiring duplicate edits to stay consistent.

---

### User Story 3 - Simpler data-management API footprint (Priority: P2)

A contributor working on the data-management API does not need nested clones or embedded sibling services for embedding, model, or scraper—those capabilities are reached only via **configured remote service endpoints** that point at the canonical deployables.

**Why this priority**: Nested duplicates confuse ownership, break CI caching, and obscure which version runs in production.

**Independent Test**: The data-management-api tree contains no embedded full copies of embedding-service, model-service, or scraper that duplicate top-level services; integration is configuration plus client code for **remote APIs only**, and fresh clone + install steps are shorter or unchanged in complexity versus the submodule era.

**Acceptance Scenarios**:

1. **Given** a fresh workspace, **When** a contributor follows setup for data-management-api, **Then** they do not initialize redundant nested service repositories for those three capabilities.
2. **Given** release tagging, **When** operators trace which scraper/embedding/model revision is live, **Then** mapping is unambiguous from **deployed service versions** and environment configuration (URLs, pinned compatibility), not from duplicate in-repo trees.

---

### User Story 4 - Ask answers return within user-tolerable time (Priority: P3)

A resident asks a typical question through the ask API (non-streaming) and receives an answer or a clear timeout message without hanging indefinitely.

**Why this priority**: Contract tests observed timeouts; user-visible latency affects trust, but scraper persistence failures are higher blast radius for operations.

**Independent Test**: Under representative load and corpus size, measure success rate and tail latency for a standard question set; compare to an agreed baseline after scraper/infra fixes (may be partially independent of consolidation).

**Acceptance Scenarios**:

1. **Given** a typical factual question, **When** the ask endpoint is invoked with default parameters, **Then** the client receives a completed response or a documented client-handled timeout—not an ambiguous hang—at least at the agreed reliability target.

---

### Edge Cases

- Persistence or job orchestration intentionally disabled in a sandbox: API should advertise unavailability with stable, documented client errors rather than leaking internal hostnames or stack traces.
- Stale or unknown job IDs: responses remain contract-stable (e.g., not-found) without 5xx.
- Partial deploy (new gateway, old workers): version skew handled via explicit errors or compatibility window documented for operators.
- Long-running questions: streaming or async patterns, if offered, remain coherent when non-streaming ask hits time limits.
- A remote scraper, embedding, or model dependency is unreachable: data-management-api returns stable, documented client errors (including timeouts) without importing or falling back to a local duplicate implementation.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: For deployments advertised as fully operational for hosted scraping jobs, the API MUST support create, list, status retrieval, and cancellation flows without undocumented `5xx` responses when inputs are valid and backing dependencies are healthy. *(Production-like validation is reflected in **SC-001** smoke and the **SC-004** live regression gate.)*
- **FR-002**: Error responses for misconfiguration or unreachable dependencies MUST be operator-debuggable without exposing raw internal infrastructure identifiers to end clients in production responses.
- **FR-003**: The monorepo MUST retain exactly one authoritative scraper **source tree** for shared business logic; secondary copies under nested application trees MUST be removed. The data-management-api MUST interact with scraping only through a **documented remote interface** to the scraper service (thin HTTP client code in-repo is acceptable; duplicated scraper business logic is not).
- **FR-004**: The data-management-api MUST NOT vendor in-tree implementations, git submodules, or in-process imports of scraper, embedding, or model **service implementations** that duplicate top-level services. For those three capabilities, integration MUST be **remote APIs only** (HTTP or equivalent), with contracts and failure modes documented for operators and client integrators.
- **FR-005**: The repository's automated live gateway contract regression suite (all phases currently required before merge) MUST pass for operations that previously failed in live runs once fixes are deployed.
- **FR-006**: Observability for job lifecycle MUST include stable correlation identifiers so operators can trace a user-reported failure across gateway and workers without redeploying custom instrumentation. The gateway MUST surface those identifiers on modal scraper HTTP responses; for Modal-hosted scrape work, the gateway MUST also pass the same identifier into `modal_scrape_job_submit` **payload** fields accepted by the scraper (and any companion env hooks documented for workers) so worker-side structured logs can include it when supported.
- **FR-007**: The ask (non-streaming) path MUST meet an operator-agreed success rate and tail-latency budget for a representative question set, or document intentional limitations and client mitigation (e.g., streaming, smaller prompts).

### Key Entities *(include if feature involves data)*

- **Scraping job**: A unit of work to fetch and process web content with metadata (source URL, owning user or tenant, status, timestamps, correlation IDs).
- **Job registry entry**: Gateway-visible record linking external job identifiers to orchestration and persistence state.
- **Ask session (logical)**: A single user question with retrieval parameters and optional reranking flags yielding an answer or timeout outcome.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In a configured production-like environment, at least **99%** of valid create/list/get/cancel sequences in a 100-iteration smoke script complete without `5xx` (excluding deliberate fault injection). *(Supports the same “healthy tier” bar as **FR-001**.)*
- **SC-002**: Maintainer survey metric: time to locate and patch scraper logic improves—measured as **one** documented primary path (binary: single authoritative location exists and is linked from root contributor docs).
- **SC-003**: Nested redundant service checkouts under data-management-api for scraper, embedding, and model are **eliminated** (binary: none remain after migration).
- **SC-004**: The automated live gateway regression gate reports **zero** failures classed as server errors for the previously failing job endpoints on the deployment used for release gating. *(Also exercises the **FR-001** modal scraper job surface under generated traffic.)*
- **SC-005**: For a fixed benchmark of **20** typical questions, non-streaming ask completes successfully in at least **18** runs, or documented timeout behavior is returned within the gateway budget for the remainder—measured over three consecutive days in staging or production-like staging.

## Assumptions

- Failures resembling unknown database hostnames indicate deployment wiring or secret rotation issues as much as code; the feature includes verifying configuration guidance and defensive handling.
- “Eliminating submodules” refers to removing nested git submodules or embedded service trees under data-management-api, not necessarily deleting top-level services.
- **Clarified (2026-04-19)**: data-management-api depends on scraper, embedding, and model **only via remote service calls**; it does not embed those services as packages inside its app tree.
- Modal or equivalent hosted compute remains acceptable behind the scenes as long as user-facing contracts and observability stay stable.
- Ask latency may depend on agent and retrieval services; some improvement may follow infra fixes but partial fulfillment is acceptable if limits are documented and tracked separately.
- **FR-007 / SC-005**: Platform or release owners record any **numeric** ask SLO beyond the SC-005 defaults (e.g. extra tail-latency caps) in `specs/003-consolidate-scraper-dm/baseline-notes-schemathesis.md` during rollout so implementers have a single agreed source of truth.

## Dependencies

- Accurate environment variables and network access from gateway/workers to persistence and job orchestration in each deployment tier.
- **Stable remote endpoints** and credentials for scraper, embedding, and model services reachable from data-management-api (and documented per environment).
- Maintainer agreement on the **canonical service deployment map**, version compatibility rules, and OpenAPI (or equivalent) contracts for those remote calls after consolidation.
