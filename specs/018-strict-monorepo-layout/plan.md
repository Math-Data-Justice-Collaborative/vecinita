# Implementation Plan: Strict Canonical Monorepo Layout

**Branch**: `018-strict-monorepo-layout` | **Date**: 2026-04-29 | **Spec**: [spec.md](./spec.md)  
**Input**: Feature specification from `specs/018-strict-monorepo-layout/spec.md`

**Note**: Path-level truth for moves is maintained in [artifacts/path-mapping.md](./artifacts/path-mapping.md).

## Path governance (FR-013, SC-006)

This **`plan.md` file** satisfies the SC-006 requirement that the implementation plan **link in body text** to the authoritative path migration map:

- **Authoritative map**: [artifacts/path-mapping.md](./artifacts/path-mapping.md) — every structural move or Render/Modal path change MUST update this file **in the same change set** as code or blueprint edits ([tasks.md](./tasks.md) enforces the same; see “Task / path-map traceability” there).
- **Executable tasks**: [tasks.md](./tasks.md) — each structural task cites `PM-xxx` row ids; spot-check SC-006 against those rows.
- **Trivial edits** (no path-map update required): defined in [spec.md](./spec.md) success criterion **SC-006** (single-file / non-deployable-root changes only).

## Summary

Reorganize the Vecinita monorepo so **each Render web service, each Modal application, and each Render-hosted frontend** has a **single canonical folder** under the agreed top-level layout (`apis/`, `modal-apps/`, `frontends/`, `packages/`, `clients/apis/`, optional `contracts/`, `infra/`, `scripts/`). Extract API-only shared persistence helpers into `packages/python/db/`, relocate generated HTTP consumers under `clients/apis/<api-name>/`, and keep **one** root `.env.local.example` and a **single** primary Render blueprint story (root `render.yaml` today, with optional `infra/` fragments later). Execution is **phased by deployable** with **`git mv` preferred** for traceability; see [research.md](./research.md). Highest-risk area: **`backend/` currently hosts both agent and gateway** with shared `src/`—splitting into `apis/agent` and `apis/gateway` needs an explicit module-boundary design before physical moves. **Module-boundary draft (T015)**: [artifacts/backend-split-inventory.md](./artifacts/backend-split-inventory.md).

## Technical Context

**Language/Version**: Python 3.11 (backend, services), TypeScript / Node 20+ (frontends), repo-wide Makefile + uv where applicable  
**Primary Dependencies**: FastAPI, uvicorn, Vite/React frontends, Modal Python SDK for Modal apps, Docker images per Render service  
**Storage**: PostgreSQL (existing); layout refactor does not change schema  
**Testing**: `make ci` from repo root; pytest (backend, services), Vitest/Playwright (frontends), Schemathesis/Pact where already wired  
**Target Platform**: Render (Docker web services + static), Modal.com (Python apps), local dev via Makefile / compose  
**Project Type**: Polyglot monorepo (multiple HTTP APIs, Modal workers, two web frontends, shared packages, generated clients)  
**Performance Goals**: No regression versus current production SLOs; layout work is neutral on latency  
**Constraints**: `make ci` must stay green across each mergeable slice; contract-first rules: HTTP **contract** / **client regeneration** stays in sync; single canonical `.env.local.example`  
**Non-functional guardrails (spec)**: **SC-003** (post-cutover incident taxonomy for “wrong folder” / duplicate copy) and **SC-005** (merge-ready CI on default branch) are product/quality bars—this plan does not restate them as build tasks. **SC-003** follow-up: during the two-week qualitative window after cutover, release/on-call tags incidents in postmortems per the repo taxonomy so “wrong service folder” / “stale duplicate copy” are distinguishable; tighten layout or docs in the same sprint if any occur. **SC-005**: implementation slices MUST still preserve merge-ready CI.  
**Scale/Scope**: ~6 production deployables (agent, gateway, chat frontend, DM frontend, DM API, Postgres managed), Modal apps (**scraper**, **embedding**, **model**) live under **`modal-apps/`** after **PM-003–PM-005** (see [artifacts/path-mapping.md](./artifacts/path-mapping.md)), submodule `apis/data-management-api`, shared `packages/openapi-clients`

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| **Community benefit** | Pass | Structural clarity speeds safe changes to public-good RAG and DM surfaces; no mission tradeoff. |
| **Trustworthy retrieval** | Pass | No change to retrieval logic by layout alone; guard against accidental behavior drift when splitting `backend/`. |
| **Data stewardship** | Pass | DM API deploy today builds from **`modal-apps/scraper`** per `render.yaml`—document and preserve semantics during moves ([research.md](./research.md)). |
| **Safety & quality** | Pass | Phased PRs + `make ci`; contract tests follow existing repo rules. |
| **Service boundaries** | Pass | Explicit goal: one deploy folder per service; shared code only via `packages/` and documented contracts ([contracts/monorepo-layout-boundary.md](./contracts/monorepo-layout-boundary.md)). **Temporary duplication** during the `backend/` → `apis/agent` + `apis/gateway` split is allowed only per boundary contract rule **2a** (short-lived, path-map documented, converging follow-up). |

**Post–Phase 1 re-check**: Design artifacts reinforce boundaries (path map, boundary contract, data model for migration rows). No violations requiring Complexity Tracking.

## Project Structure

### Documentation (this feature)

```text
specs/018-strict-monorepo-layout/
├── plan.md                 # This file
├── research.md             # Phase 0
├── data-model.md           # Phase 1
├── quickstart.md           # Phase 1
├── spec.md
├── artifacts/
│   └── path-mapping.md     # Authoritative legacy → canonical map (FR-013)
└── contracts/
    └── monorepo-layout-boundary.md
```

### Source Code (repository root)

**Current (abbreviated, pre-refactor)** — see `artifacts/path-mapping.md` for the full mapping table.

```text
backend/                    # Agent + gateway shared tree; Dockerfiles for agent + gateway
frontends/chat/             # Chat UI submodule (Render: vecinita-frontend)
frontends/data-management/  # Data-management UI submodule (Render: vecinita-data-management-frontend-v1)
modal-apps/scraper/         # Scraper + (today) image used for vecinita-data-management-api-v1 on Render
modal-apps/embedding-modal/
modal-apps/model-modal/
apis/data-management-api/   # Submodule; FastAPI DM API source
packages/openapi-clients/   # Generated TS/Python clients (to migrate under clients/apis/)
render.yaml                 # Canonical blueprint (FR-008): stays at root; see quickstart for infra/ option
Makefile
```

**Target (canonical)** — aligns with spec FR-001–FR-005:

```text
apis/
├── gateway/
├── agent/
└── data-management-api/

modal-apps/
├── scraper/
├── embedding-modal/
└── model-modal/

frontends/
├── chat/
└── data-management/

packages/
├── python/
│   ├── db/
│   ├── modal-shared/       # optional
│   ├── http-clients/       # optional
│   └── shared-schemas/     # optional
└── ts/
    ├── eslint-config/      # optional
    └── ui-kit/             # optional

clients/apis/
├── gateway/
├── agent/
└── data-management-api/

contracts/                  # repo-level HTTP snapshots, Pact docs (optional)
infra/                      # optional fragments / docker helpers
scripts/                    # repo automation not tied to one deployable
specs/
Makefile
.env.local.example
render.yaml                   # primary; or infra/ + pointer (documented choice)
```

**Structure Decision**: Adopt the **target tree** above as the end state. Reach it through **phased moves** ordered by dependency risk (Modal apps and frontends before splitting shared `backend/`, unless research-driven ordering changes). All moves are **tracked in `artifacts/path-mapping.md`**; `tasks.md` (from `/speckit.tasks`) must reference row IDs.

**Ordering coherence (tasks vs research)**: Prefer completing the **scraper** folder move (**PM-003 / T011**) before the **data-management-api submodule** relocation (**PM-006 / T014**) so two teams rarely edit overlapping paths under legacy `services/` in the same window; if parallelized, coordinate merges to avoid drift.

**Optional subtrees** (`packages/python/modal-shared`, `http-clients`, `shared-schemas`, `packages/ts/eslint-config`, `ui-kit`): **Out of scope for v1** of this refactor unless a path-map row is added—see [spec.md §Assumptions](./spec.md#assumptions) (“introduced incrementally”). No additional acceptance criteria until a row exists.

**Assumptions (mirror)**: Naming collisions, phased migration, `render.yaml` vs `infra/`, and Spec Kit mechanics follow [spec.md §Assumptions](./spec.md#assumptions). Rename policy: **one rename across `apis/`, `clients/apis/`, and docs per collision**, recorded in `artifacts/path-mapping.md`.

## Complexity Tracking

> No constitution violations requiring justification. Large shared `backend/` split is engineering risk, captured in research and path map—not a principle waiver.

---

## Phase 0: Research

**Output**: [research.md](./research.md) — migration sequencing, `git mv` policy, Render/DM API image caveat, client relocation strategy.

## Phase 1: Design & Contracts

**Outputs**:

- [data-model.md](./data-model.md) — entities for migration tracking (path map row, deployable binding).
- [contracts/monorepo-layout-boundary.md](./contracts/monorepo-layout-boundary.md) — rules for what may live in `packages/` vs deploy folders.
- [quickstart.md](./quickstart.md) — how to update the path map, run `make ci` after moves, and where Render entrypoints live during transition.

**Agent context**: `.cursor/rules/specify-rules.mdc` updated to reference **this** `plan.md` (see SPECKIT markers).

## Phase 2

**Not produced by `/speckit.plan`**: run **`/speckit.tasks`** to generate `tasks.md` with each task citing `artifacts/path-mapping.md` rows.
