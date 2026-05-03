# Feature Specification: OpenAPI SDK clients and standardized service URLs

**Feature Branch**: `015-openapi-sdk-clients`  
**Created**: 2026-04-24  
**Status**: Draft  
**Input**: User description: "Strictly eliminate all URL calls to Modal; use only function or method calls. Swap HTTP clients for SDKs generated with OpenAPI Generator (Python pydantic v1, TypeScript Node, TypeScript Axios). Initialize generation for the three APIs (Gateway, Data Management, Agent) and their consumers. Deprecate and remove configuration that pointed application code at Modal-hosted inference or duplicate model/embedding base URLs. Standardize runtime connection configuration to a single allowed set of environment variables for database, Render-hosted gateway and agent, OpenAPI schema locations, and the Data Management API."

## Clarifications

### Session 2026-04-24

- Q: For Modal-hosted workloads, what integration scope applies—may Modal-deployed code use Modal-assigned HTTP (e.g. web endpoints / inference HTTP), or is HTTP to Modal forbidden everywhere in checked-in code? → A: **Option B — Strict everywhere:** no HTTP(S) to Modal-assigned hostnames from any checked-in code (including Modal app modules); only Modal SDK / RPC-style orchestration (e.g. `.remote()`, function calls), not `requests`/`httpx`/`fetch`/Axios to Modal hosts.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Operators deploy with one clear connection surface (Priority: P1)

As an operator or integrator, I configure the system using a small, documented set of variables so every component knows how to reach the database, the gateway, the agent, the data-management API, and where to fetch each service’s OpenAPI document for code generation and contract checks—without scattered legacy URLs for Modal inference or duplicate model endpoints.

**Why this priority**: Misconfigured base URLs are a primary source of production outages and security mistakes; consolidating configuration reduces operational risk before any client refactor ships.

**Independent Test**: With only the allowed variables set in a staging environment, smoke tests for chat, retrieval, and ingestion still reach the correct backends; grepping the deployment configuration shows zero references to deprecated Modal or duplicate model URL variables.

**Acceptance Scenarios**:

1. **Given** a fresh deployment manifest, **When** an operator sets only the approved connection variables, **Then** all services start and health checks pass without requiring any deprecated URL variables.
2. **Given** documentation for environment variables, **When** a reviewer audits the list, **Then** every required outbound connection is mapped to exactly one variable from the approved set (or to Modal SDK orchestration where Modal compute is used, with no Modal HTTP base URLs in configuration).

---

### User Story 2 - Developers call remote HTTP APIs through contract-faithful clients (Priority: P1)

As a developer working in Python or TypeScript, I import generated clients for the Gateway, Data Management, and Agent HTTP APIs so request paths, payloads, and auth headers stay aligned with each service’s published OpenAPI document; I do not hand-roll URLs against those three APIs in application code.

**Why this priority**: Contract drift between services causes subtle bugs and broken bilingual or retrieval flows; generated clients encode the contract at build time.

**Independent Test**: A change that breaks the OpenAPI contract fails in CI via regeneration or contract tests before merge; application modules contain no raw string paths for those three APIs outside the generated layer.

**Acceptance Scenarios**:

1. **Given** an updated OpenAPI document for one of the three APIs, **When** clients are regenerated, **Then** the monorepo compiles and tests that exercise those clients pass or surface intentional breaking changes.
2. **Given** application code that previously constructed HTTP calls manually to gateway, data-management, or agent, **When** the feature is complete, **Then** those call sites use the generated client surface only.

---

### User Story 3 - Modal is invoked only via SDK functions, not HTTP URLs (Priority: P1)

As a developer, when I need Modal compute (for example inference or embeddings hosted on Modal), I invoke Modal only through Modal SDK orchestration (e.g. `.remote()`, `.spawn`, `.map`, and `@app.function` composition). I do not use HTTP or HTTPS clients toward Modal-assigned hostnames from any checked-in code, including code inside Modal app modules.

**Why this priority**: The user explicitly requires eliminating URL-based access to Modal, which enforces a single integration style and avoids leaking deployment URLs into config.

**Independent Test**: Static analysis and repository search (plus CI policy where applicable) show **no** HTTP or HTTPS client usage whose destination is a Modal-assigned hostname; Modal entry points appear only as SDK calls. Deprecated Modal URL environment variables are absent.

**Acceptance Scenarios**:

1. **Given** code paths that previously used environment variables for Modal HTTP endpoints, **When** the feature ships, **Then** those variables are unused and documented as removed, with behavior preserved via SDK-only orchestration (or via Gateway/Agent/Data Management HTTP per FR-002 when the work runs outside Modal).
2. **Given** a developer adding a new Modal-backed capability, **When** they wire it up, **Then** they use Modal SDK patterns documented for this repo—**not** new URL env vars, **not** hard-coded `https://` URLs to Modal hosts, and **not** generic HTTP clients pointed at Modal.

---

### User Story 4 - Documentation and published docs reflect the new model (Priority: P2)

As a contributor, I can read internal docs and the GitHub Pages workflow output so that connection setup, client regeneration, and CI steps describe the OpenAPI-driven clients and the approved environment variables—including how schema URLs feed generation and docs.

**Why this priority**: Reduces onboarding friction and prevents reintroduction of deprecated variables.

**Independent Test**: Docs build succeeds; a new teammate can follow the doc to regenerate clients and configure staging without referring to removed variables.

**Acceptance Scenarios**:

1. **Given** the docs pipeline, **When** it runs on main, **Then** it references the three canonical schema URLs and does not instruct readers to set deprecated Modal URL variables for application connectivity.

---

### Edge Cases

- **Schema fetch failures**: When `GATEWAY_SCHEMA_URL`, `DATA_MANAGEMENT_SCHEMA_URL`, or `AGENT_SCHEMA_URL` is **set** but unreachable in CI or locally, generation or contract checks MUST fail loudly with actionable errors rather than silently reusing stale artifacts. An **explicit offline mode** (documented flag or target) MAY use only committed schema snapshots or checked-in OpenAPI copies **named in docs**; invoking that mode MUST be deliberate—there is no silent fallback when URLs are configured.
- **Partial migration**: If one language stack lags, the feature MUST still forbid **new** uses of deprecated env vars in any touched code path, MUST track remaining handwritten Gateway/DM/Agent HTTP call sites in a maintained inventory until **SC-002** is met, and MUST drive deprecated **names** to **zero** in application code, deployment templates, and committed examples per **SC-001** / **FR-005** regardless of migration percentage.
- **Secrets in URLs**: For this feature, requirements extend to **documentation and logging**: connection strings (`DATABASE_URL`) and other URL-shaped secrets MUST NOT appear verbatim in logs, screenshots, or published examples. Broader secret-rotation or vault policy is out of scope beyond that.
- **Modal HTTP is out of scope for shortcuts**: Even when Modal’s platform exposes HTTP for inference, web endpoints, or similar ([Modal](https://modal.com) product surfaces), this feature adopts **SDK-only** integration in **all** checked-in code. Any capability that cannot meet FR-001 without HTTP to Modal MUST be **redesigned** (e.g. compose Modal functions via SDK, or expose behavior only through Render-hosted HTTP APIs per FR-002) **or** **escalated** with a merge-blocking issue, named owner, and explicit tech-lead or maintainer sign-off before release—**not** shipped behind undocumented HTTP to Modal hosts.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: **All** checked-in code—including sources built and deployed as Modal apps, whether entrypoints run inside Modal workers or on Render—MUST NOT perform HTTP or HTTPS requests to **Modal-assigned hostnames** or otherwise target Modal-hosted workloads via HTTP clients (`requests`, `httpx`, `urllib`, `fetch`, Axios, etc.). **Modal-assigned hostnames** means hosts matching the repository-maintained pattern list enforced for **SC-005** (see `specs/015-openapi-sdk-clients/contracts/modal-http-ban-sc005.md` and `config/modal_http_ban_patterns.txt`). Modal compute MUST be reached only through Modal SDK orchestration (e.g. `.remote()`, `.spawn`, `.map`, direct function composition within Modal’s execution model) with **no** dependency on hard-coded or env-configured Modal `https://` base URLs. This rule does **not** forbid HTTP(S) to **Render-hosted** Gateway, Agent, or Data Management services using **FR-004** base URLs and generated clients. Callers outside Modal that need model or embedding behavior MUST use Gateway, Agent, or Data Management HTTP APIs using the approved environment variables and generated OpenAPI clients (FR-002, FR-004–FR-005).
- **FR-002**: All HTTP traffic from **application logic** to the **Gateway**, **Data Management**, and **Agent** REST surfaces MUST go through HTTP client code generated from each service’s canonical OpenAPI description, so paths and models are not duplicated by hand in call sites. **Application logic** means product and service code under `backend/src/`, `services/`, `frontend/`, and `apps/data-management-frontend/` excluding (a) generated OpenAPI client output trees agreed in feature contracts, (b) vendored third-party packages, and (c) tests and fixtures whose sole purpose is to mock HTTP or assert on generated types—those exclusions MUST NOT be used to smuggle production call sites past **FR-002**. Breaking changes to generated surfaces MUST follow the repository’s normal migration or compatibility discipline for stable HTTP APIs.
- **FR-003**: The repository MUST define a repeatable process (documented and automatable in CI where applicable) to fetch each canonical OpenAPI JSON document and regenerate typed HTTP clients for every language runtime in this monorepo that calls those three APIs, with outputs versioned or ignored per existing repository conventions for generated code. When **all** of `GATEWAY_SCHEMA_URL`, `DATA_MANAGEMENT_SCHEMA_URL`, and `AGENT_SCHEMA_URL` are unset in a CI context (e.g. fork pull requests), workflows MAY **skip** regeneration with an explicit logged skip line; when **any** schema URL is set, unreachable URLs MUST fail loudly per the **Schema fetch failures** edge case—skips never substitute for silent reuse of stale artifacts.
- **FR-004**: Runtime configuration for cross-service and database connectivity MUST use only the following environment variables for those purposes: `DATABASE_URL`, `RENDER_GATEWAY_URL`, `RENDER_AGENT_URL`, `GATEWAY_SCHEMA_URL`, `DATA_MANAGEMENT_API_URL`, `DATA_MANAGEMENT_SCHEMA_URL`, `AGENT_SCHEMA_URL`.
- **FR-005**: The following environment variables MUST NOT be read, written, or required by application code, deployment manifests, or example env files after migration is complete: `MODAL_OLLAMA_ENDPOINT`, `MODAL_EMBEDDING_ENDPOINT`, `VECINITA_MODEL_API_URL`, `VECINITA_EMBEDDING_API_URL`, `EMBEDDING_SERVICE_URL`. Any behavior that depended on them MUST be preserved through Modal SDK calls or through calls to the Gateway, Agent, or Data Management APIs using the approved variables.
- **FR-006**: Operators MUST be able to configure staging and production solely with the approved variables plus any secrets unrelated to this feature (existing auth tokens, etc.), without additional base-URL variables for the same logical destinations.
- **FR-007**: Contract or smoke tests appropriate to this change MUST demonstrate that generated clients can successfully reach `RENDER_GATEWAY_URL`, `DATA_MANAGEMENT_API_URL`, and `RENDER_AGENT_URL` when those services are available in a test environment. This **supplements** **FR-002** (reachability and wiring); it does **not** waive the requirement that routine application traffic use generated clients only.
- **FR-008**: Documentation surfaced to contributors (including GitHub Pages where this repo publishes API or integration docs) MUST list the approved variables, describe how schema URLs drive client generation, and MUST NOT present the deprecated variables as current.

### Key Entities *(include if feature involves data)*

- **Connection profile**: The set of approved URLs and connection strings an environment uses: database DSN, gateway base URL, agent base URL, data-management base URL, and three schema document locations used for generation and validation.
- **Generated API client package**: Per-language, per-service module tree produced from OpenAPI that encapsulates HTTP details for Gateway, Data Management, or Agent.
- **Modal invocation**: A callable entry point reached exclusively through the Modal SDK’s RPC-style orchestration APIs—not via HTTP(S) to Modal-assigned hosts—for code that runs inside or coordinates with Modal’s execution model, per project conventions and clarification Session 2026-04-24.

## Success Criteria *(mandatory)*

### Measurable Outcomes

Identifiers (**SC-001**, **SC-005**, **SC-002**, etc.) are **stable cross-references** into specs, plans, and tasks; their numeric order in this section does **not** imply execution priority or dependency ordering.

- **SC-001**: In the main branch after delivery, automated search of the repository (excluding generated vendor trees if explicitly quarantined in ignore rules) reports **zero** references to `MODAL_OLLAMA_ENDPOINT`, `MODAL_EMBEDDING_ENDPOINT`, `VECINITA_MODEL_API_URL`, `VECINITA_EMBEDDING_API_URL`, and `EMBEDDING_SERVICE_URL` in application code, infrastructure templates, and committed example environment files. Exclusion globs or paths for generated/vendor trees MUST be **version-controlled** alongside the search script or workflow (not ad hoc per operator run) so the gate is reproducible.
- **SC-005**: The **same** validation pipeline as **SC-001** (or a documented sibling job in the same workflow family) reports **zero** violations of **FR-001** using the hostname/pattern list in `config/modal_http_ban_patterns.txt` and rules in `specs/015-openapi-sdk-clients/contracts/modal-http-ban-sc005.md`, so HTTP(S) clients cannot target Modal hosts without CI failure once the gate is enabled.
- **SC-002**: At least **95%** of **previous** hand-written HTTP call sites to Gateway, Data Management, or Agent in **maintained application packages**—`backend/src/`, `apis/data-management-api/`, `modal-apps/scraper/`, `frontend/`, and `apps/data-management-frontend/`, excluding only generated-client output directories and vendored third-party code as listed in feature contracts—are migrated to generated-client usage. The **denominator** (“previous”) is the first committed migration inventory for this feature (see tasks **T028**) unless a release PR explicitly revises baseline with rationale. Exceptions MUST be documented with owner and removal date.
- **SC-003**: A new contributor can follow published documentation to regenerate all three client families from the three schema URLs and run the **documented** local or CI validation flow for this feature (install generator pin, run codegen verify or equivalent, run the named smoke/unit targets in **quickstart**) in **under 30 minutes** on typical hardware. **In scope for the time box**: dependency install for those steps, OpenAPI fetch/generation, and the named validation targets. **Out of scope**: full monorepo `make ci`, first-time container image pulls, and downloading large model weights.
- **SC-004**: Staging deployments that use only the approved connection variables complete an end-to-end user journey (e.g., authenticated chat or a representative ingestion path) with **no** increase in p95 error rate compared to the pre-change baseline over a **one-week** observation window, or any regression is triaged and documented before release. **Verification**: This criterion is **operator-led** (not a unit test); implementers MUST add and follow **`docs/deployment/SC004_STAGING_RELEASE_CHECKLIST.md`** (tasks **T045**), which MUST name **metrics source** (e.g. Render service metrics, gateway structured logs), **baseline commit and timestamp**, **rollback owner**, and **sign-off role** (e.g. on-call or tech lead) so p95 comparison is auditable. **SC-004** and **SC-002** measure different things and impose **no** ordering dependency on each other relative to **SC-005**.

## Assumptions

- **Normative vs informational**: **FR-002**, **FR-003**, **FR-005**, and **FR-008** are normative. Bullet choices below (generator IDs, CLI pins, folder names) are **implementation defaults**; they MAY change without amending this spec **provided** the normative outcomes (typed OpenAPI-derived clients, drift checks, forbidden vars removed, docs accurate) still hold.
- **Code generation tooling**: The project will standardize on [OpenAPI Generator](https://openapi-generator.tech/) with these generator IDs for the three HTTP APIs: `python-pydantic-v1`, `typescript-node`, and `typescript-axios`, matching upstream documentation for each ([python-pydantic-v1](https://openapi-generator.tech/docs/generators/python-pydantic-v1), [typescript-node](https://openapi-generator.tech/docs/generators/typescript-node), [typescript-axios](https://openapi-generator.tech/docs/generators/typescript-axios)). HTTP client behavior for browser or Node consumers that need Axios aligns with the [Axios request API](https://axios-http.com/docs/api_intro). **FR-001** applies to **browser and Node** TypeScript the same as Python when static analysis can resolve HTTP client targets (exact enforcement scope is documented in the ban contract).
- Wrapper scripts or CI jobs MAY pin a specific OpenAPI Generator CLI version; planners will wire `.github/workflows` (including docs publication, e.g. `docs-gh-pages.yml` where applicable) so schema-driven docs and client regeneration stay consistent.
- The three canonical OpenAPI JSON documents are reachable at the URLs given by `GATEWAY_SCHEMA_URL`, `DATA_MANAGEMENT_SCHEMA_URL`, and `AGENT_SCHEMA_URL` in environments where generation runs; those documents are authoritative over any hand-maintained copies except short-lived local edits during upstream fixes.
- Modal SDK usage patterns already exist or will be introduced in the smallest set of integration modules so that product features do not import Modal directly from unrelated UI layers.
- **Modal integration posture (clarified 2026-04-24)**: The project rejects Modal’s HTTP-oriented integration paths **in this repository’s checked-in code** in favor of SDK-only orchestration on Modal and OpenAPI-generated HTTP clients toward Render-hosted services. If upstream Modal capabilities are HTTP-first, planners MUST map them to SDK composition or to Gateway/Agent/Data Management boundaries rather than adding HTTP calls to Modal hosts in-repo.
- Removing deprecated URL variables does not eliminate the need for non-URL secrets (API keys, tokens); those remain governed by existing security practices.
- **Constitution alignment**: Service boundaries (gateway, agent, data management) remain explicit; new coupling crosses a boundary only through generated clients derived from published OpenAPI, supporting verifiable delivery and contract testing called for in the project constitution.
