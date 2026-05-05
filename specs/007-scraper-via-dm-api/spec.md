# Feature Specification: Route scraper access through data management backend

**Feature Branch**: `008-scraper-via-dm-api`  
**Created**: 2026-04-22  
**Status**: Draft  
**Input**: User description: "We're moving the scraper interface, instead of being a Modal.com endpoint is going to be accessed through apis/data-management-api/ we can call the function calls from the modal service services/scraper/ but not the endpoint. Ensure that the all the backend calls from apps/data-management-frontend/ are going to apis/data-management-api/ and that all the backend calls from frontend/ are going to the gateway please."

## Clarifications

### Session 2026-04-22

- Q: Which posture should the specification mandate for Modal-backed scraper, embedding, and model work orchestrated by our backends (DM API and agent)? → A: **Functions-first (Modal-aligned)** — backends invoke named deployed functions; Modal API tokens only server-side; no DM or main frontend bundles contain Modal tokens or Modal HTTP base URLs for those capabilities; optional documented HTTP-to-Modal only for local/non-prod developer convenience.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Operators manage scraping without calling the scraper host directly (Priority: P1)

An operator uses the data-management experience to start or monitor scraping-related work. Their browser only communicates with the data-management backend; that backend is responsible for reaching the scraper execution capability using supported server-to-server mechanisms. The operator never needs a browser-visible URL or credential path to the scraper’s public web entrypoint.

**Why this priority**: Direct browser access to a separate scraper endpoint fragments security boundaries, complicates auditing, and duplicates configuration; consolidating behind the data-management backend matches stewardship and operational expectations.

**Independent Test**: From the data-management UI, complete a primary scraping workflow (for example: initiate work, view status, handle a common failure) while network inspection shows no client requests targeting the scraper’s public web entrypoint, **or** use equivalent automated proof per **SC-001**.

**Acceptance Scenarios**:

1. **Given** an operator authenticated for data management, **When** they perform a scraping action exposed by the data-management UI, **Then** the browser sends requests only to the data-management backend (not to the scraper’s public web entrypoint).
2. **Given** a scraping workflow in progress, **When** the operator refreshes status from the UI, **Then** updates are obtained through the data-management backend without the browser calling the scraper host directly.

---

### User Story 2 - Main product users stay on the gateway boundary (Priority: P1)

A resident or community user uses the main web application. Any server-backed actions they trigger from that application go through the organization’s API gateway, not directly to internal service URLs that bypass the gateway.

**Why this priority**: The gateway is the agreed public boundary for the main app; bypass undermines auth, rate limiting, observability, and contract discipline.

**Independent Test**: From the main frontend, exercise representative authenticated flows that hit the backend; confirm all such traffic targets the gateway base URL configuration, not internal service hosts—or use equivalent automated proof per **SC-002**.

**Acceptance Scenarios**:

1. **Given** a user session in the main frontend, **When** they trigger a feature that requires backend data, **Then** the client issues that request to the gateway entrypoint as configured for the main app.
2. **Given** a misconfiguration attempt (wrong internal base URL), **When** the app is built or configured for production-like settings, **Then** automated checks or documented release steps prevent shipping with a non-gateway backend URL for the main frontend.

---

### User Story 3 - Scraper execution remains callable for orchestration only (Priority: P2)

Platform automation or the data-management backend invokes scraper, embedding, and model-related ingest work through **named, server-side programmatic interfaces** on the hosted compute platform (for example Modal **deployed Functions**). External clients do not rely on the platform’s former public HTTP entrypoints for those responsibilities.

**Why this priority**: Keeps heavy or privileged execution on the scraper side while narrowing the attack and configuration surface exposed to the internet.

**Independent Test**: In an integration or staging environment, a server-side caller can complete a scraper orchestration path without using the deprecated public web entrypoint, and behavior matches operator-visible outcomes in the data-management UI.

**Acceptance Scenarios**:

1. **Given** the data-management backend orchestrates a scrape, **When** execution runs, **Then** the scraper is driven through the supported server-side programmatic path, not the retired browser-facing entrypoint.
2. **Given** documentation for operators and maintainers, **When** they follow connection guidance, **Then** it describes data-management backend and gateway routes—not direct scraper web URLs for clients.

---

### Edge Cases

- **Scraper unavailable**: The data-management backend returns clear, user-appropriate feedback when the scraper cannot be reached; the UI does not silently fail or expose raw internal errors.
- **Embedding or model path unavailable**: The same standard applies when embedding or model steps fail mid-ingest—operators see actionable status without raw upstream dumps in the UI.
- **Hosted platform throttling or cold start**: Backends surface understandable progress, backoff, or retry guidance; operators are not expected to interpret low-level platform diagnostics.
- **Partial rollout**: If some environments still expose the old entrypoint temporarily, operators are informed which environment is authoritative and old paths are not used by shipped frontends.
- **Bookmarked or hard-coded URLs**: Old scraper web URLs must not be required for any supported user journey; migration notes cover removing saved links from runbooks.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The data-management web client MUST send all of its backend-bound traffic to the data-management backend only (no direct browser calls to the scraper’s public web entrypoint for features owned by data management).
- **FR-002**: The main web application client MUST send all of its backend-bound traffic to the organization’s API gateway only (no direct browser calls to internal service hosts for supported user flows).
- **FR-003**: Together with **FR-001**, scraping and related orchestration that today or historically relied on a public web entrypoint on the hosted scraper platform MUST be exposed to clients through the data-management backend’s surface instead (so operators never depend on a separate scraper web surface for those capabilities).
- **FR-004**: In **production and staging**, the data-management backend MUST orchestrate **scraping, embedding ingestion, and model-backed ingestion** using **server-side programmatic invocation of named, deployed functions** on the hosted compute platform (Modal-aligned), not through browser-reachable platform web entrypoints for those responsibilities.
- **FR-005**: Operators MUST be able to complete documented scraping workflows from the data-management UI without credentials or configuration that only apply to direct scraper web access.
- **FR-006**: Observability for scraping and **related ingest** workflows (including embedding and model steps orchestrated by the data-management backend) MUST remain sufficient for audit: which actor or backend initiated work, timestamps, and correlation identifiers traceable across the data-management backend and hosted execution, consistent with data stewardship expectations in the project constitution.
- **FR-007**: Client applications (data-management web and main web) MUST NOT ship, embed, or require end-users to supply **hosted compute platform** API tokens or direct platform HTTP base URLs for scraping, embedding, or model orchestration.
- **FR-008**: In **production and staging**, the **agent service** (reached from the gateway) MUST use the **same** server-side programmatic invocation pattern for **Modal-hosted** model and embedding work—not platform web entrypoints for those responsibilities.
- **FR-009**: **Non-production** environments MAY use a **documented** HTTP fallback to platform-hosted web apps for developer convenience only; **production and staging** acceptance criteria and smoke tests MUST NOT depend on that fallback.

### Key Entities *(include if feature involves data)*

- **Scraping workflow**: A unit of work (start, status, completion, cancellation as applicable) initiated by an operator or backend and visible through the data-management experience.
- **Data-management backend**: The service boundary that the data-management web client uses for all backend operations, including scraping orchestration.
- **API gateway**: The public backend entrypoint used by the main web application for supported flows.
- **Scraper execution environment**: The deployment that performs scraping; reachable for orchestration via programmatic interfaces, not as the primary client-facing HTTP surface for these flows.
- **Hosted compute platform** (e.g. Modal): The vendor environment where scraper, embedding, and model functions are deployed; **production/staging** integration uses **named deployed functions** invoked from backends only, per clarifications.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In a production-like configuration, **100%** of sampled data-management UI backend requests for **primary flows** target the data-management backend hostname only. **Sampled** means the requests or **stand-in assertions** enumerated for those flows in the agreed **primary-flow release matrix** (automated test cases, optional E2E steps, and/or explicit manual checklist rows). Verification MAY use **scripted automated tests** of resolved client configuration (unit/integration) plus **optional browser end-to-end** exercises when the product already ships them; manual smoke checklists MAY supplement. **Browser-level network sampling** is recommended where feasible but is not the sole acceptable proof method.
- **SC-002**: In a production-like configuration, **100%** of sampled main-frontend backend requests for **primary flows** target the gateway hostname only. **Sampled** is defined the same way as in **SC-001** (primary-flow release matrix: automated cases, optional E2E, and/or manual checklist rows). Verification MAY use the **same pattern** as **SC-001**: scripted automated tests of resolved client configuration, **optional** browser end-to-end exercises when shipped, and **optional** manual smoke checklists; **browser-level network sampling** is recommended where feasible but is not the sole acceptable proof method.
- **SC-003**: Zero required user journeys for scraping management rely on the scraper’s deprecated public web entrypoint (verified by test matrix and release checklist, **aligned with the primary-flow release matrix** used for **SC-001** / **SC-002** so the same rows cover routing and deprecated-URL avoidance).
- **SC-004**: Within one release cycle of shipping the change, operator-facing runbooks and onboarding instructions contain no mandatory direct scraper web URLs for supported workflows (audit of documentation).
- **SC-005**: For **production and staging** builds of both web clients, release verification (automated scan or checklist) confirms **no embedded hosted-compute platform API tokens** and **no embedded platform HTTP base URLs** required for scraping, embedding, or model orchestration in client bundles.

## Assumptions

- The “main frontend” and “data-management frontend” are distinct deployable clients with separate base-URL configuration; each can be validated independently.
- **Production and staging** use the clarified **functions-first** posture for the hosted compute platform; **non-production** may use a documented HTTP fallback for developers only (**FR-009**).
- Authentication and authorization for scraping actions remain enforced at the data-management backend (and gateway for main-app flows) as they are today or stricter; this feature does not relax those gates.
- Naming paths like `apps/data-management-frontend/`, `frontend/`, `apis/data-management-api/`, and `services/scraper/` refer to the repository’s agreed ownership boundaries. **Modal** is the concrete hosted compute platform referenced in clarifications; integration details remain in implementation plans and contracts.
