# Feature Specification: Gateway live reliability and contract coverage

**Feature Branch**: `001-gateway-live-schema`  
**Created**: 2026-04-18  
**Status**: Draft  
**Input**: User description: "Fix backend API errors deployed to Render (use Render MCP / debug skills as needed) and improve to achieve 100% schema coverage for the API, per live Schemathesis CLI failures (modal job routes returning 500; TraceCov below 100%)."

## Clarifications

### Session 2026-04-18

- Q: For Postgres used by modal-backed scraper job routes, which configuration surfaces are in
  scope for a mandatory fix? → A: **B** — **Gateway Render environment only**; changes to Modal or
  scraper **worker secrets** are **out of scope** for mandatory delivery of this feature.
- Q: For TraceCov **responses** toward **100%**, what is mandatory? → A: **A** — **Full** expansion:
  **every operation included** in the live gateway pass has **complete OpenAPI `responses`**
  documentation the coverage gate expects (typical success, client errors, and structured server
  error bodies the gateway may return), except entries explicitly waived in the approved exception
  register (FR-004).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Reliable job operations from the public gateway (Priority: P1)

An operator or integrator uses the hosted community gateway to submit or inspect scraping-related
jobs (including paths backed by remote workers). They expect documented operations to complete
without generic “server error” responses when the deployment is healthy and credentials are valid.

**Why this priority**: Broken job flows block ingestion and erode trust in the public-good corpus
pipeline; they show up immediately in automated contract runs.

**Independent Test**: Run the project’s live automated API contract suite against the staging
gateway; the job submission, list, status, and cancel journeys that are in scope for that suite do
not return 5xx solely because of misconfigured infrastructure connectivity.

**Acceptance Scenarios**:

1. **Given** a healthy deployment and valid auth where required, **When** a client submits a job
   through the gateway using a valid example payload, **Then** the gateway returns a success-class
   response or a documented client error—not an undocumented server error caused by unreachable
   backing services for standard configuration.
2. **Given** an existing job identifier returned by the system, **When** a client requests status or
   cancellation, **Then** the gateway returns a success-class or documented not-found/conflict
   response—not a 5xx caused by the backing worker failing to open its operational datastore.

---

### User Story 2 - Contract exploration reaches full coverage gate (Priority: P2)

A release owner runs the automated gateway contract pass that includes schema-coverage reporting.
They need the pass to meet the organization’s **100%** coverage threshold on dimensions the gate
enforces (so the run is merge- or release-safe without waiving quality).

**Why this priority**: Prevents silent drift between the published contract and exercised behavior;
unblocks CI-style gates tied to TraceCov.

**Independent Test**: After operational fixes, a single contract pass on the same gateway
OpenAPI reaches **100%** on each dimension the gate reports (operations, parameters, keywords,
examples, **responses**) or the spec documents an explicit, approved exception list with rationale.
The **responses** dimension MUST reach **100%** through **full** per-operation OpenAPI documentation
for **all included operations** (per Clarifications **A**), not only a baseline subset.

**Acceptance Scenarios**:

1. **Given** the live gateway OpenAPI and the standard contract configuration, **When** the
   contract pass completes, **Then** schema coverage meets the **100%** threshold or a written
   exception lists each remaining gap with owner approval.
2. **Given** an operation previously at **0%** parameter coverage in the report, **When** the pass
   runs after changes, **Then** that operation no longer appears as fully missed for required
   dimensions unless explicitly excluded by policy.
3. **Given** every operation **selected** for the live pass, **When** the schema coverage report is
   generated, **Then** the **responses** dimension shows **100%** for those operations—meaning each
   can emit only **documented** status codes for the exercised checks—or each gap appears in the
   approved exception register with rationale.

---

### User Story 3 - Fewer false negatives in contract warnings (Priority: P3)

An engineer triages contract output. They want fewer “missing test data” and “schema validation
mismatch” warnings for routes that are healthy but hard to fuzz without realistic seeds.

**Why this priority**: Reduces noise so real regressions stand out; improves time-to-diagnosis.

**Independent Test**: For a defined list of high-traffic read routes, contract warnings about
missing resources drop after supplying realistic identifiers or tightening examples—without hiding
real bugs.

**Acceptance Scenarios**:

1. **Given** documented hooks or env seeds for registry and document preview identifiers, **When**
   the contract pass runs with those set, **Then** repeated 404-only warnings for those routes drop
   measurably compared to the baseline run attached to the issue.

---

### Edge Cases

- Modal or other workers cold-start slowly; contract suite must distinguish timeout from DNS or
  auth misconfiguration.
- Jobs legitimately not found (unknown UUID) should remain **404** (or documented conflict), not
  **500**.
- Reindex or other upstream-triggering routes may remain excluded from default live passes by
  policy; coverage expectations must respect that exclusion without silently lowering the gate for
  included routes.
- If **500** responses are caused by workers using **non-resolvable internal** database hostnames,
  remediation limited to **gateway Render env** may be insufficient; the runbook (SC-004) MUST
  state when to escalate **outside** this feature’s mandatory scope (e.g., worker secret updates).

## Requirements *(mandatory)*

<!--
  Constitution: align with `.specify/memory/constitution.md` — community-good RAG, trustworthy
  behavior, data stewardship, safety/quality, service boundaries. This feature improves operational
  reliability of public gateway job flows and contract quality gates.
-->

### Functional Requirements

- **FR-001**: The system MUST allow clients to submit scraping-related jobs through the gateway
  without returning a **500** series response when the **Render gateway service** environment is
  configured per validated deployment guidance for this feature (see Clarifications: gateway-only
  mandatory scope).
- **FR-002**: The system MUST support listing and reading job status for scraping-related jobs
  through the gateway without **500** responses under the same gateway-environment assumptions as
  FR-001.
- **FR-003**: The system MUST support cancelling scraping-related jobs through the gateway with
  documented outcomes (success, not found, or conflict) rather than **500** for valid identifiers
  under the same gateway-environment assumptions as FR-001.
- **FR-004**: The automated gateway contract pass (live OpenAPI, default phase set excluding
  stateful unless enabled) MUST achieve **100%** schema coverage on each dimension enforced by the
  project’s coverage gate for all operations **included** in that pass, or the delivery includes an
  approved exception register mapping each gap to a decision.
- **FR-005**: Operators MUST be able to diagnose connectivity-related failures from error payloads
  or logs without raw stack traces leaking secrets (timestamps and clear error class remain
  acceptable). The operator runbook (SC-004) MUST distinguish **gateway Render env** remediation (in
  mandatory scope) from **worker secret / DSN** remediation (out of mandatory scope per
  Clarifications).
- **FR-006**: For **every operation included** in that pass, the **published gateway OpenAPI** MUST
  document the **`responses`** entries needed so the TraceCov **responses** dimension can reach
  **100%**—including typical **2xx**, **4xx**, and structured **5xx** JSON bodies the gateway may
  return for that operation—unless waived with rationale in the exception register tied to FR-004.

### Key Entities *(include if feature involves data)*

- **Gateway job (scraping path)**: Identifier returned to clients; used for status and cancel flows.
- **Contract pass configuration**: Which routes are in scope, example budgets, hooks/seeds, and
  coverage thresholds. **Included** operations are the set over which **FR-006** applies in full
  (Clarifications **A**).
- **Gateway Render environment**: Environment variables and secrets attached to the **gateway**
  service on Render that this feature may change or document; **Modal / scraper worker secrets** are
  a separate entity and are **not** in mandatory change scope.
- **Deployment connectivity policy**: Rules for which database hostnames **each runtime** may use;
  mandatory fixes in this feature apply to **gateway-side** configuration only.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: On three consecutive live contract runs after the fix, **zero** failures classified as
  “server error” for **POST** job submit, **GET** job list, **GET** job by id, and **POST** cancel on
  the scraping-related gateway paths that the run exercises (same host and auth configuration).
- **SC-002**: At least one post-fix contract run shows **100%** on operations, parameters, keywords,
  examples, and responses dimensions in the schema coverage summary for the gateway pass, or the
  exception register (FR-004) is published with sign-off.
- **SC-003**: Baseline “missing valid test data” warning count for the four routes called out in the
  baseline log drops by **50%** or more once recommended seeds/hooks are applied, measured on a
  single back-to-back comparison run.
- **SC-004**: A published operator runbook (or deployment doc update) describes how to distinguish
  infrastructure connectivity failures from application defects for these flows in **10 or fewer**
  numbered steps, and receives maintainer sign-off in the delivery PR.

## Assumptions

- Staging gateway host and OpenAPI URL remain the default target for the live contract script unless
  otherwise specified.
- **Mandatory delivery** changes are limited to the **Render gateway** service environment (per
  Clarifications **B**). Updates to **Modal** or **scraper worker** database secrets are **not**
  assumed or required for sign-off of this feature; persistent **500**s may remain until a
  follow-up initiative if root cause is worker-side DNS.
- `POST /scrape/reindex` (or equivalent) may stay excluded from the default live pass by existing
  policy; full **100%** coverage and **FR-006** apply to **every operation the pass selects**, not
  to paths outside that selection. **Responses** documentation is **full** for that included set
  (Clarifications **A**).
- Bearer or bootstrap env vars for live runs are available to testers when auth is enabled on the
  gateway.
