# Feature Specification: Wire chat frontend to gateway/agent and align data-management stack

**Feature Branch**: `005-wire-services-dm-front`  
**Created**: 2026-04-21  
**Status**: Draft  
**Input**: User description: wire the main chat `frontend/` to the gateway and agent services using values defined in the unified root `.env` (and documented templates such as `.env.local.example`); connect `apps/data-management-frontend` to `services/data-management-api` so runtime configuration, request/response models, and API contracts stay aligned.

## Clarifications

### Session 2026-04-21

- Q: For CI, what must automated frontend↔backend integration verification include? → A: Option C — PR pipeline uses mock/fixture-first frontend integration; real-stack integration runs on main, nightly, or an explicitly triggerable workflow.
- Q: For chat (gateway + agent), what is the mandatory contract-testing approach in addition to frontend integration tests? → A: Option B — add consumer-driven contracts (e.g. Pact) verified from `frontend/` in CI.
- Q: For the data-management frontend ↔ API boundary, should consumer-driven contracts (Pact) apply there too? → A: Option B — yes, add Pact for `apps/data-management-frontend` ↔ data-management API in parallel with chat.

### Session 2026-04-22 (post-analysis)

- **Streaming vs Pact (I1)**: **Pact** consumers MUST cover **non-streaming** HTTP request/response pairs for chat against the gateway (and agent-facing paths the client uses). **SSE / streaming** chat turns MUST be validated by **FR-009** Playwright and/or **FR-006** real-stack integration—not mandatory inside Pact unless the project later adopts a Pact-compatible streaming pattern.
- **Typed DTO source of truth (U1)**: When **FR-004** introduces **OpenAPI-driven codegen** (or equivalent generated types), generated output becomes the **authoritative** TypeScript shape for DM client + Pact matchers; any hand-written types in **FR-010** modules are **interim scaffold** only and MUST be **replaced or thin-re-export** generated types once codegen is merged—**no** long-lived duplicate definitions.
- **Schemathesis regression (C1)**: Existing **gateway and agent** Schemathesis coverage defined in `TESTING_DOCUMENTATION.md` / `backend/schemathesis.toml` MUST **remain** in CI as a regression gate when this feature ships; new DM/modal-jobs Schemathesis scope **adds** to that baseline, not replaces it.
- **U1 (chat vs DM typed surfaces)**: **FR-004** / OpenAPI codegen (**tasks.md** **T029**) applies first to the **DM** client (`rag-api`, DM Pact). **Chat** interim types (**T005** / **T007**) are **not** superseded by **T029**; they stay scaffold until a future feature adds chat-side codegen. **No** ordering conflict: **T029** must complete before removing **T006** bodies and before the post-codegen half of **T008**.

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Chat app reaches gateway and agent consistently (Priority: P1)

As a developer running the chat stack locally or against Render, I want `VITE_GATEWAY_URL`, proxy targets, and documented backend URLs (`AGENT_SERVICE_URL`, `RENDER_GATEWAY_URL`, `RENDER_AGENT_URL`, schema URLs) to resolve to the same logical API surface so the UI can load agent config, send chat requests, and stream responses without manual URL hacking.

**Why this priority**: Without correct wiring, the primary product surface is unusable.

**Independent Test**: Start gateway + agent (or point at deployed hosts), set only template-safe env values, load chat UI, complete **(1)** one **non-stream** chat request with Pact/contract or integration evidence that paths match `/api/v1` expectations (**FR-007** / Pact is **non-streaming HTTP only** per **Clarifications §2026-04-22**), and **(2)** one **streaming** chat turn validated via **Playwright** (preferred) or real-stack manual/DevTools checks—**(2)** MUST NOT be asserted via Pact unless the project later adopts a Pact-compatible streaming pattern.

**Acceptance Scenarios**:

1. **Given** local gateway on port 8004 and `frontend/.env` with `VITE_GATEWAY_URL=/api` and matching Vite proxy target, **When** the user opens chat, **Then** agent health/config and chat calls succeed through the proxy.
2. **Given** production-like absolute URLs for gateway (from env templates, not committed secrets), **When** the SPA is served from its own origin, **Then** `agentService` resolution (`resolveGatewayUrl` / `normalizeAgentApiBaseUrl`) produces a reachable base URL and streaming works within configured timeouts.

---

### User Story 2 — Data management UI talks to the bundled API (Priority: P1)

As an operator using the data-management dashboard, I want `VITE_VECINITA_SCRAPER_API_URL` (and optional `VITE_VECINITA_GATEWAY_URL` for gateway modal jobs) to target the process started from `services/data-management-api` so scrape job CRUD and health checks hit the correct service.

**Why this priority**: Misaligned URLs produce silent failures or wrong backends.

**Independent Test**: Run data-management API on configured port, set frontend env to that base URL, open dashboard, verify `/health` and job endpoints succeed.

**Acceptance Scenarios**:

1. **Given** API listening at `http://localhost:8005` and frontend env pointing there, **When** the dashboard loads, **Then** scraper diagnostics report a valid configured URL and job list requests use `${apiBase}/jobs` (or gateway modal-jobs root when feature flag is on).
2. **Given** CORS on the API allows the frontend dev origin, **When** the browser calls the API, **Then** responses are not blocked by CORS for documented dev ports.

---

### User Story 3 — Models and contracts stay aligned (Priority: P2)

As a maintainer, I want a repeatable way to keep TypeScript client shapes and Python/FastAPI models in sync for the data-management boundary (and documented parity for gateway OpenAPI where the chat frontend depends on it).

**Why this priority**: Prevents drift that only shows up in production.

**Independent Test**: Run **FR-004** (DM OpenAPI/schema alignment), **FR-008** (DM consumer contracts), and **FR-007** (chat consumer contracts) in CI or locally after API or client change; failures block merge until contracts are updated.

**Acceptance Scenarios**:

1. **Given** an OpenAPI export from the data-management API surface the UI uses, **When** a field is added server-side, **Then** the alignment workflow fails until the frontend (or generated types) is updated.
2. **Given** gateway and agent OpenAPI plus **consumer-driven contracts** (e.g. **Pact**) for chat client interactions, **When** chat features add or change HTTP usage, **Then** **both** provider-side tests (e.g. **Schemathesis** per `TESTING_DOCUMENTATION.md`) **and** consumer contract verification catch incompatible changes before release.
3. **Given** **Pact** (or equivalent) interactions for **DM** scrape/health (and **gateway modal-jobs** paths when enabled), **When** the DM API or `rag-api` client changes HTTP behavior, **Then** **FR-008** consumer verification **and** **FR-004** alignment checks catch drift before release.

---

### Edge Cases

- Relative `VITE_GATEWAY_URL=/api` on non-localhost hosts must behave consistently with Render deployment patterns (documented in `agentApiResolution` / `apiBaseResolution`).
- DM frontend Docker/runtime injection (`window.__VECINITA_ENV__`) vs Vite `import.meta.env` must receive the same logical URLs.
- Optional gateway modal jobs (`VITE_USE_GATEWAY_MODAL_JOBS`) must not break legacy direct-API mode when unset.
- **CI cost**: Default PR checks must not require a full Docker Compose gateway+agent+DM stack; real-stack jobs are allowed to be slower and run outside the default PR merge path.
- **Pact workflow**: Broker vs **local pact file** publishing must be documented so contributors know how to run consumer tests offline and how CI publishes or verifies pacts without leaking secrets.
- **Two consumers**: Chat (`frontend/`) and DM (`apps/data-management-frontend/`) both run consumer contracts; documentation MUST state whether they share one **Pact broker** and naming/tag strategy or use **isolated** flows so pactfiles and provider verifications do not collide.
- **CORS documentation location**: CORS allowlist guidance for the DM API MUST live in **existing** published docs (prefer `services/data-management-api/README.md` or root env template comments); avoid requiring new files under the submodule unless they already exist in the tree.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Document and implement a single mapping from unified env templates (root `.env.local.example`, `frontend/.env.example`, `apps/data-management-frontend/.env.example`) to runtime services so `make` / Compose / Render setups do not contradict each other for gateway, agent, and DM API ports.
- **FR-002**: Chat frontend MUST consume gateway base URL via `VITE_GATEWAY_URL` or `VITE_BACKEND_URL` with behavior consistent with existing `frontend/src/app/services/agentService.ts` and resolution helpers.
- **FR-003**: Data-management frontend MUST resolve API base via `VITE_VECINITA_SCRAPER_API_URL` (and optional gateway vars) consistent with `apps/data-management-frontend/src/app/api/scraper-config.ts`.
- **FR-004**: Add or extend an automated check (script, CI job, or test) that validates alignment between data-management API OpenAPI (or shared schema package) and the TypeScript types or fetch layer the dashboard uses for scrape jobs and related entities.
- **FR-005**: Gateway and agent HTTP surfaces used by the chat app MUST satisfy **both**: (a) server-side OpenAPI contract tests (e.g. **Schemathesis**) per `TESTING_DOCUMENTATION.md`, and (b) **FR-007** consumer-driven contracts from `frontend/`. DM HTTP surfaces MUST satisfy **FR-004** and **FR-008**. Any intentional gap MUST be documented with rationale and an alternate verification plan. **Regression**: existing **gateway + agent** Schemathesis jobs already in CI MUST keep passing when this feature merges; new work only **extends** coverage (e.g. DM OpenAPI / modal-jobs paths).
- **FR-006 (integration testing in CI)**: On **pull requests**, automated frontend tests MUST run without a mandatory live gateway+agent (or full DM) stack—using mocks, MSW, fixtures, or fast client-level tests. At least one **documented** workflow (default branch after merge, **cron** schedule, or **`workflow_dispatch`**) MUST run **real-stack** integration tests that start or target real gateway and agent processes (and DM API when DM wiring changes), so cross-service URL and proxy behavior is exercised regularly.
- **FR-007 (consumer-driven contracts, chat)**: `frontend/` MUST run **consumer-driven contract tests** (e.g. **Pact**) covering agreed gateway and agent interactions **for non-streaming HTTP** (request/response JSON). **Consumer** verification MUST run on **pull requests** without requiring a full live stack (mock server, recorded interactions, or equivalent). **Provider** verification against gateway/agent (or approved stubs) MUST be automated and documented—including whether it is merge-blocking or runs on default branch—so provider and consumer expectations cannot drift silently. **Streaming/SSE** remains out of mandatory Pact scope per **Clarifications §2026-04-22** and MUST be covered by **FR-009** / **FR-006**.
- **FR-008 (consumer-driven contracts, DM)**: `apps/data-management-frontend/` MUST run **consumer-driven contract tests** (e.g. **Pact**) covering agreed interactions with the data-management API (direct **scraper** base, including **`/jobs`** and **`/health`**, and **gateway modal-jobs** paths when `VITE_USE_GATEWAY_MODAL_JOBS` is enabled—model as separate pact interactions or providers as appropriate). **Consumer** verification MUST run on **pull requests** without a mandatory full DM API stack where mocks suffice; **provider** verification against the DM API (or approved stubs) MUST be automated and documented like **FR-007**.
- **FR-009 (Playwright E2E)**: **Playwright** MUST cover **smoke compatibility** for the chat app (gateway-backed chat path) and the data-management dashboard (DM API + optional gateway modal-jobs), using isolated tests and documented env bases; heavy suites MAY shard in CI. Placement follows **FR-006** (PR-optional vs main/nightly real-stack). **Principle III** (see **Constitution alignment** below for how this feature narrows scope): suites SHOULD assert at least minimal **accessibility** signals on primary flows (e.g. focus reaches the main chat input and one navigation control via keyboard; `html[lang]` present or documented locale hook) and SHOULD leave hooks for **bilingual** copy checks where the app exposes locale toggles—without blocking merge on full i18n coverage.
- **FR-010 (typed integration DTOs)**: TypeScript types or **Zod** schemas for JSON bodies used by `agentService`, `rag-api`, and **Pact** consumers MUST share **one authoritative definition per product line** so compile-time checks prevent drift from OpenAPI/Pydantic semantics (see `data-model.md` §Typed testing artifacts). When **FR-004** codegen is enabled, **generated types** supersede hand-written duplicates per **Clarifications §2026-04-22**; Pact matchers MUST import the same module as production fetch code.

### Key Entities *(include if feature involves data)*

- **ServiceEndpointConfig**: logical names (`gateway`, `agent`, `dm_api`, `dm_frontend`) with env var names and example placeholder values only; a **single catalog table** tying each logical name to template variables MUST be maintained in `specs/005-wire-services-dm-front/contracts/env-wiring-chat-gateway-agent.md` (and cross-linked from `quickstart.md` per **SC-001**).
- **ScrapeJob** (and related DTOs): fields exposed on `/jobs` (or gateway proxy path) that the DM frontend lists/creates; must match server models.

### Assumptions

- Operators use template files (`.env.example`, `.env.local.example`) for documentation; real `.env` is gitignored and not copied into specs.
- `services/data-management-api` continues to expose the scraper-compatible HTTP surface expected by the DM frontend unless a migration is explicitly specified in a follow-up spec.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A new contributor can follow `quickstart.md` for this feature and reach a working chat + DM dashboard against local services without reading scattered README fragments for URL wiring alone.
- **SC-002**: **FR-004** OpenAPI/schema alignment checks pass on **main** for the DM API ↔ frontend boundary; **FR-008** provider verification meets the documented merge or default-branch policy.
- **SC-003**: The repository documents where **real-stack** integration runs (branch, schedule, or manual trigger) and that path completes successfully for the chat gateway+agent stack; default **PR** checks remain **mock/fixture-first** per FR-006.
- **SC-004**: Pull-request CI runs and passes the **Pact** (or equivalent) **consumer** contract suite for the chat frontend’s covered gateway/agent interactions; provider verification outcomes are visible per the documented **FR-007** workflow.
- **SC-005**: Pull-request CI runs and passes the **Pact** (or equivalent) **consumer** contract suite for the data-management frontend’s covered DM API (and optional gateway modal-jobs) interactions; provider verification outcomes are visible per the documented **FR-008** workflow.
- **SC-006**: Documented **Playwright** E2E workflow(s) pass on the non-PR path (or optional PR shard) for both chat and DM critical journeys per **FR-009**; failures block release until wiring or tests are fixed.

## Constitution alignment

This feature reinforces **service boundaries** (explicit HTTP contracts, **consumer-driven** guarantees, and env-driven wiring) and **safety & quality** (contract tests). It does not change corpus ingestion rules; documentation must continue to discourage committing secrets (see **data stewardship**). **Principle III** requires bilingual and accessibility expectations to be first-class **where UX or content is affected**; this feature implements that minimum through **FR-009** as **documented SHOULD-level checks** in Playwright (**tasks.md** **T015**, **T021**): keyboard reachability, `html[lang]` / locale hooks where present, and hooks for bilingual copy where toggles exist—**without** merge-blocking full i18n coverage. Governance: scope is **explicitly narrowed** for this feature, not a silent downgrade of constitution **MUST** elsewhere.
