# Feature Specification: Strict Canonical Monorepo Layout

**Feature Branch**: `018-strict-monorepo-layout`  
**Created**: 2026-04-29  
**Status**: Draft  
**Input**: User description: "I want to refactor the repo to follow this structure strictly. Where APIs are render API deploys, modal-apps are Modal deploys, frontends are Render site deploys, packages are local clients that can be re-used, as part of this we may need to pull out reusable code for different aspects like the database client. Please. [canonical tree: apis/, modal-apps/, frontends/, packages/, clients/apis/, contracts/, infra/, scripts/, specs/, Makefile, render.yaml, .env.local.example]"

## Clarifications

### Session 2026-04-29

- Q: Where must the authoritative current path → canonical path mapping be maintained through the refactor? → A: Under this feature directory (e.g. `specs/018-strict-monorepo-layout/artifacts/path-mapping.md` or equivalent); implementation plan and tasks must trace moves from it (Option A).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Find the right home for a change (Priority: P1)

A maintainer needs to change behavior that belongs to a specific internet-facing API, a background Modal workload, or a user-facing site. They open the repository and quickly land in exactly one top-level area that matches that responsibility, without guessing among legacy paths.

**Why this priority**: Wrong placement causes duplicate logic, broken deploy wiring, and review churn; this is the daily cost the restructure removes.

**Independent Test**: Given a short list of hypothetical edits (e.g., “adjust HTTP contract for the public gateway,” “tune embedding batch size,” “change chat navigation”), reviewers can each point to a single folder under the agreed top-level layout without contradiction.

**Acceptance Scenarios**:

1. **Given** the path-mapping artifact in this feature directory and an arbitrary legacy path still in use mid-migration, **When** a contributor needs the canonical target folder, **Then** they resolve it from that artifact (or from `plan.md` / `tasks.md` rows that cite it) without a second conflicting source.
2. **Given** the refactored tree is documented at repository root, **When** a contributor is asked where gateway HTTP behavior lives, **Then** they identify `apis/gateway/` (or its documented successor name) as the sole primary location.
3. **Given** the same tree, **When** a contributor is asked where the scraper Modal application lives, **Then** they identify `modal-apps/scraper/` as the sole primary location.
4. **Given** the same tree, **When** a contributor is asked where the chat user interface lives, **Then** they identify `frontends/chat/` as the sole primary location.

---

### User Story 2 - One folder, one deployable (Priority: P1)

Operations and release managers need a predictable mapping from repository folders to deployment targets: each Render API service, each Modal app, and each Render-hosted frontend has a single obvious folder that owns its build and runtime configuration.

**Why this priority**: Ambiguous ownership causes misconfigured services and failed rollbacks.

**Independent Test**: For each production deployable named in this spec, there is exactly one folder that is the source of truth for that deployable’s entrypoint and deploy metadata, with no second copy required for a normal release.

**Acceptance Scenarios**:

1. **Given** the gateway is deployed as a Render web service, **When** a release is cut for the gateway only, **Then** all changes required for that release are contained under `apis/gateway/` plus shared libraries pulled in as dependencies (not a parallel copy of the same service).
2. **Given** the scraper runs as a Modal application, **When** a release is cut for the scraper only, **Then** the Modal deploy is driven from `modal-apps/scraper/` alone at the folder level (shared code may live under `packages/`).
3. **Given** the chat site is deployed on Render, **When** a release is cut for the chat frontend only, **Then** the deploy is driven from `frontends/chat/` alone at the folder level.

---

### User Story 3 - Reuse without tangles (Priority: P2)

Developers need to extract cross-cutting concerns (for example database session helpers used only by HTTP APIs) into shared packages so Modal apps and APIs do not each fork the same logic, while keeping service boundaries clear per the project constitution.

**Why this priority**: Duplicated persistence or client code drifts and breaks contracts across services.

**Independent Test**: A shared concern that appears in two deployables today can be listed once under `packages/` (or the agreed language subtree) and consumed as a dependency without creating a second “hidden” copy inside a deploy folder.

**Acceptance Scenarios**:

1. **Given** database access helpers are intended for API services only, **When** they are extracted, **Then** they live under `packages/python/db/` (or the agreed equivalent) and both `apis/agent/` and `apis/data-management-api/` depend on that package rather than duplicating files.
2. **Given** optional cross-language or cross-surface models are needed, **When** teams add them, **Then** they place shared request/response shapes under `packages/python/shared-schemas/` only when those shapes are genuinely shared, not as a dump for service-specific types.

---

### User Story 4 - Contract-first consumers (Priority: P2)

Teams that build frontends or internal callers need generated or thin typed HTTP surfaces organized per API, so contract changes are visible in one predictable place under the repository.

**Why this priority**: Aligns with constitution expectations on stable surfaces and reduces hand-written drift.

**Independent Test**: For each first-party HTTP API in `apis/`, there is a matching subtree under `clients/apis/<api-name>/` that is the canonical home for generated or hand-maintained consumer types for that API.

**Acceptance Scenarios**:

1. **Given** the data-management API publishes a machine-readable HTTP contract, **When** consumer code is regenerated or updated after that contract changes, **Then** the consumer surface is updated under `clients/apis/data-management-api/` in the same change set as the contract change (per repository delivery rules).
2. **Given** a frontend needs to call the gateway, **When** engineers look for the typed client, **Then** they find it under `clients/apis/gateway/` without searching unrelated packages.

---

### User Story 5 - Supporting material stays discoverable (Priority: P3)

Contributors need optional contract snapshots, infrastructure glue, and automation scripts to remain first-class but not mixed into deployable roots.

**Why this priority**: Keeps deploy folders lean while preserving auditability.

**Independent Test**: HTTP contract snapshots, Pact artifacts, or similar live under `contracts/` (when used); Render blueprint fragments or Docker helpers live under `infra/` when centralized; one-off automation lives under `scripts/`.

**Acceptance Scenarios**:

1. **Given** the team keeps HTTP contract snapshots for review, **When** they add or update a snapshot, **Then** it is stored under `contracts/` (or documented exception) rather than inside application source trees unless a deliberate exception is recorded in the spec’s Assumptions.
2. **Given** CI or Render references a root blueprint, **When** operators look for the canonical blueprint location, **Then** they find it at repository root `render.yaml` or under `infra/` with a short root-level pointer in documentation agreed in planning.

---

### Edge Cases

- A proposed directory move appears in `plan.md` or `tasks.md` but not in the feature path-mapping artifact: the update MUST NOT merge until the artifact and plan/tasks stay consistent in the same change set.
- **Rollback / failed migration PR**: Reverting or abandoning a layout PR is done with normal version control (e.g., revert the merge). The path map MUST be restored to a consistent state in the **same revert PR or an immediate follow-up** (row `status` and `notes` match the tree again). Out of scope: runtime database rollback—this feature is repository layout only.
- A deployable temporarily needs code from two legacy locations during migration: migration plan MUST name a cutover step and forbid indefinite dual ownership.
- A shared package is imported only by Modal: it still lives under `packages/` (e.g., `packages/python/modal-shared/`) rather than inside one Modal app folder, unless the team documents an exception with rationale.
- Generated client output conflicts with hand edits: constitution and delivery rules require regeneration or a documented manual sync process—the spec assumes planning will pick one source of truth per client subtree.
- Optional subtrees (`eslint-config`, `ui-kit`, `http-clients`) are absent at milestone one: the tree MUST still validate against the mandatory folders in Requirements; optional folders MAY be added later without breaking the rule set.

## Requirements *(mandatory)*

Constitution alignment: service boundaries (Principle V) MUST remain explicit—shared code MUST not re-couple services without a documented contract; automated verification appropriate to risk MUST stay green (Principle IV).

### Functional Requirements

- **FR-001**: The repository MUST expose a top-level `apis/` directory. Each immediate child folder under `apis/` MUST correspond to at most one Render-deployed HTTP API service (gateway, agent, data-management-api, and any future API added the same way).
- **FR-002**: The repository MUST expose a top-level `modal-apps/` directory. Each immediate child folder under `modal-apps/` MUST correspond to at most one Modal-deployed application (scraper, embedding-modal, model-modal, and future Modal apps the same way).
- **FR-003**: The repository MUST expose a top-level `frontends/` directory. Each immediate child folder under `frontends/` MUST correspond to at most one Render-deployed static site or web frontend (chat, data-management, and future frontends the same way).
- **FR-004**: The repository MUST expose a top-level `packages/` directory for shared libraries not owned by a single deployable, organized by language (`packages/python/`, `packages/ts/`). Shared database session and migration glue used by APIs MUST be extractable to `packages/python/db/` (or the planned equivalent) rather than duplicated across `apis/*` folders.
- **FR-005**: The repository MUST expose a top-level `clients/` directory with `clients/apis/` mirroring first-party HTTP APIs; each API name under `apis/` MUST have a matching consumer subtree under `clients/apis/<same-name>/` for generated or thin typed HTTP surfaces, kept in lockstep when contracts change (per repository policy). **Interim note**: During phased migration, generated clients MAY temporarily remain under a legacy path **only** while a path-map row documents the transition and **FR-011** requires a `cutover_date` if that interim state would still exist after **more than one merge to the repository default branch** that touches the same consumer layout (see Assumptions).
- **FR-006**: The repository MUST retain `specs/` for feature specifications and MUST retain a root `Makefile` as the primary developer entry for common automation.
- **FR-007**: The repository MUST retain exactly one canonical committed environment example at repository root: `.env.local.example` (per unified environment variable policy). New keys MUST be added only there.
- **FR-008**: Deployment blueprint files MUST have a single documented canonical location: either root `render.yaml` or `infra/` with an obvious pointer from the root README or quickstart produced in planning—no competing “primary” blueprint paths.
- **FR-009**: Optional directories `contracts/` (contract snapshots, Pact, shared contract docs) and `infra/` (blueprint fragments, Docker helpers, CI glue) MUST be used when those concerns exist; they MUST NOT be required to duplicate logic already owned by `apis/`, `modal-apps/`, or `frontends/`.
- **FR-010**: `scripts/` MUST remain (or be introduced) as the home for repository-local automation that is not part of a deployable’s runtime package layout.
- **FR-011**: After the refactor, no production deployable’s primary source MUST remain only under a legacy path unless listed in a time-bounded migration inventory with an owner and removal date (documented in planning artifacts, not left implicit).
- **FR-012**: Cross-service shared request/response shapes MUST live under `packages/python/shared-schemas/` only when genuinely shared across multiple deployables; service-private shapes remain with that service.
- **FR-013**: For the duration of this refactor, the repository MUST maintain exactly one authoritative **current path → canonical path** mapping as a committed artifact under this feature’s directory (for example `specs/018-strict-monorepo-layout/artifacts/path-mapping.md`). The implementation plan (`plan.md`) and task list (`tasks.md`) for this feature MUST trace every structural move or legacy-path retirement to that artifact so reviews have a single source of truth.

### Key Entities

- **Deployable (Render API)**: A long-running HTTP service deployed from exactly one folder under `apis/`.
- **Deployable (Modal app)**: A Modal application deployed from exactly one folder under `modal-apps/`.
- **Deployable (Render frontend)**: A site or web UI deployed from exactly one folder under `frontends/`.
- **Shared package**: Versioned or path-based library under `packages/` consumed by two or more deployables or clients, without embedding a second copy inside deploy folders.
- **Consumer surface**: Typed or generated HTTP client material under `clients/apis/<api>/` tied to that API’s contract.
- **Contract artifact**: Machine-readable HTTP contract snapshot or consumer–provider test artifact stored under `contracts/` when the team maintains those materials.
- **Path migration map**: The single authoritative table or list under this feature directory that records legacy repository paths and their canonical targets (and status), referenced by plan and tasks.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In a blind folder quiz with at least five mixed tasks covering gateway, agent, data-management API, scraper Modal app, and chat UI, maintainers unfamiliar with the pre-refactor layout achieve at least 90% correct folder placement on first attempt after reading a single one-page tree overview (measured in onboarding dry-runs or recorded sessions).
- **SC-002**: For every production Render API and Modal app and Render frontend in scope at cutover, **release documentation**—defined as the combination of **`README.md` (deploy / layout section)**, **`render.yaml` service entries** (`dockerfilePath` / `dockerContext` or equivalent), and **`DEPLOYMENT_QUICK_START.md` or successor deployment doc at repo root**—lists exactly one owning folder path per deployable with zero “also copy from” paths required for a standard deploy.
- **SC-003**: For two consecutive weeks after cutover, zero production incidents are attributed to “wrong service folder” or “stale duplicate copy” per postmortem or incident taxonomy (qualitative gate; if incidents occur, each must be resolved by tightening layout or docs within the same sprint).
- **SC-004**: The canonical environment example file remains a single root `.env.local.example`; audits find zero additional committed example env files introduced for the same purpose during this refactor.
- **SC-005**: Automated verification required for merge readiness (repository’s documented CI entry) passes on the default branch at refactor completion and remains mandatory for follow-up changes touching moved paths.
- **SC-006**: Before any PR that moves or retires more than **trivial path depth**—where **trivial** means single-file edits, typo fixes, or path-only changes that do **not** relocate a deployable root, shared client root, or top-level `apis/` / `modal-apps/` / `frontends/` / `clients/apis/` subtree—the path migration map exists under this feature directory, **`plan.md` links to it in body text (not only via this spec)**, and a spot-check of five randomly chosen moves from `tasks.md` each cites a corresponding row or section in that map with no contradictory second mapping document elsewhere in the repo.

## Assumptions

- Existing service names (gateway, agent, data-management-api, scraper, embedding-modal, model-modal, chat, data-management frontend) map one-to-one to the folders named in the user-provided tree unless planning discovers a naming collision, in which case planning renames consistently across `apis/`, `clients/apis/`, and docs.
- Optional packages (`modal-shared`, `http-clients`, `shared-schemas`, `eslint-config`, `ui-kit`) may be introduced incrementally; mandatory layout for this feature is the presence and rules of the top-level directories and the mandatory `packages/python/db/` extraction goal for API database helpers—not that every optional subtree exists on day one.
- `render.yaml` at repository root is acceptable if `infra/` holds only fragments, provided FR-008’s single-canonical-location rule is satisfied via documentation.
- Feature specs under `specs/` continue to use existing numbering conventions; this spec does not change Spec Kit mechanics.
- Migration may be phased; functional requirements apply to the completed state unless explicitly marked as time-bounded in planning (FR-011 inventory).
- The path migration map artifact path uses this feature folder name (`specs/018-strict-monorepo-layout/`); if the folder is renamed, FR-013 and SC-006 apply to the renamed directory consistently.
- **Release cycle (for FR-005 interim clients)**: Means **one merge to the default branch** that includes changes to the generated-client layout or its path-map row for that consumer; “more than one release cycle” means **two such merges** would still leave clients on a legacy path without completing **T020** (then require `cutover_date` per FR-011 on the path-map row).
