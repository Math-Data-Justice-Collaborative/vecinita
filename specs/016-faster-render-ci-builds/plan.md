# Implementation Plan: Faster Render builds and GitHub Actions CI

**Branch**: `016-faster-render-ci-builds` | **Date**: 2026-04-28 | **Spec**: [spec.md](./spec.md)  
**Input**: Feature specification and **Clarifications Session 2026-04-28** (preserve functionality and gates; **time-only** optimization).

## Summary

Cut **median wall-clock** for (1) **GitHub Actions** pull-request and branch validation and (2) **Render** Docker **build phases** for `render.yaml`-managed services, while meeting **FR-004**, **FR-007**, **FR-008**, and **SC-003** (no silent removal of required checks; same merge-blocking and correctness intent as baseline). Work is **measurement-first** (**FR-001**), then **caching**, **layering**, **path-based job skipping** where provably safe, **parallelism** across independent jobs, and **documentation** (**FR-005**, **FR-006**). Baselines, caps, and **FR-004** waivers MUST live in the **governance artifact** path named in [spec.md](./spec.md) Definitions. Heavy suites such as **Schemathesis + TraceCov** (see [research.md](./research.md)) are prime candidates for **structure** (split, schedule, or scope) without lowering OpenAPI coverage where the constitution and `TESTING_DOCUMENTATION.md` require it.

## Technical Context

**Language/Version**: Python **3.10+** / **3.11+** on backend and services; Node **20** for frontends; Docker builds on Render.  
**Primary Dependencies**: **uv** (locked sync), **npm ci**, **Docker BuildKit** on Render; **pytest**, **Schemathesis**, **tracecov** for API schema suites.  
**Storage**: N/A for this feature (metrics in GitHub/Render UIs or exported artifacts).  
**Testing**: **`make ci`** remains the local merge gate; **`.github/workflows/test.yml`** (and related workflows) mirror or subset it; Schemathesis targets under `backend/tests/integration/`.  
**Target Platform**: **GitHub Actions** (`ubuntu-22.04` runners); **Render** (`dockerfilePath` / `dockerContext` in `render.yaml` and service-local blueprints).  
**Project Type**: **Monorepo** — `backend/`, `services/*`, `frontend/`, `apps/data-management-frontend/`, `packages/`, `.github/workflows/`, `render.yaml`.  
**Performance Goals**: **≥20%** median improvement vs documented baseline for at least one high-frequency CI category and one code-only Render build class (**FR-002**, **FR-003**, **SC-001**, **SC-002**); cold-start and dependency-change segments tracked separately per spec edge cases.  
**Constraints**: No net loss of defect/security coverage (**FR-007**); traceable path skips (**FR-006**); **autoDeployTrigger: checksPass** behavior preserved unless explicitly redesigned with the same safety intent.  
**Scale/Scope**: All Render web services using `backend/Dockerfile` or service-specific Dockerfiles; primary CI entry `test.yml` plus quality/render helper workflows touched only when aligned with path filters and caching.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|--------|
| **Community benefit** | **Pass** | Indirect: faster iteration on RAG/data-management features; no mission tradeoff. |
| **Trustworthy retrieval** | **Pass** | No change to attribution or retrieval logic. |
| **Data stewardship** | **Pass** | Build/CI timing only; ingestion policies unchanged. |
| **Safety & quality** | **Pass** | Plan explicitly forbids coverage-reducing shortcuts; constitution **local CI** / contract-test expectations preserved or strengthened via measurement. |
| **Service boundaries** | **Pass** | Optimizations stay in CI/Docker/build configs; cross-service contracts unchanged unless a faster **equivalent** check replaces one (**FR-004**). |

**Post–Phase 1 re-check**: [contracts/ci-path-triggers.md](./contracts/ci-path-triggers.md) documents path-to-job intent for audits; [contracts/render-docker-build-layers.md](./contracts/render-docker-build-layers.md) documents Render build caching expectations; [data-model.md](./data-model.md) defines baseline and skip-decision entities.

## Project Structure

### Documentation (this feature)

```text
specs/016-faster-render-ci-builds/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── ci-path-triggers.md
│   └── render-docker-build-layers.md
├── checklists/
│   ├── requirements.md
│   └── ci-velocity.md
└── tasks.md              # /speckit.tasks (not produced by /speckit.plan)
```

### Source code (primary touchpoints)

```text
.github/workflows/
  test.yml                    # Job matrix, caches, path filters, parallelism
  quality-gate.yml            # If redundant with test.yml — align or dedupe safely
  render-deploy.yml           # Only if CI deploy hooks affect perceived latency

Makefile                      # test-schemathesis* targets, quality-full / ci composition

backend/
  Dockerfile                  # Layer order; deps before sources for cache
  tests/integration/          # Schemathesis — optional pytest marks / split for CI tiers

render.yaml                   # dockerfilePath, dockerContext per service
apps/data-management-frontend/render.yaml
docs/deployment/
  RENDER_SHARED_ENV_CONTRACT.md   # Update only if build env vars change
TESTING_DOCUMENTATION.md      # Document any new CI tiers or local/CI parity expectations
```

**Structure Decision**: Treat **`.github/workflows`** + **`Makefile`** + **`backend/Dockerfile`** + root **`render.yaml`** as the primary implementation surface; frontends’ **`package-lock.json`** caching already partially applied in `test.yml` — extend patterns to **uv**/**submodules** where wins are clear.

## Complexity Tracking

> No constitution violations requiring justification.

## Phase 0: Research

Consolidated in [research.md](./research.md) — GitHub Actions caching and path filters, Render Docker layer caching, Schemathesis/TraceCov runtime tradeoffs (including split vs combined runs), and documentation of rejected “speed-only” shortcuts that would violate **FR-007**.

## Phase 1: Design & contracts

- [data-model.md](./data-model.md) — baseline window, change category, timing sample, skip decision.  
- [contracts/ci-path-triggers.md](./contracts/ci-path-triggers.md) — path globs ↔ jobs (audit for **FR-006**).  
- [contracts/render-docker-build-layers.md](./contracts/render-docker-build-layers.md) — dependency-copy order, BuildKit notes, multi-service Dockerfile reuse.  
- [quickstart.md](./quickstart.md) — how to capture baselines from GitHub and Render and run scoped `make` targets locally.

## Next step

Follow **`tasks.md`** (Phases 1–2 baselines, then US1 → US2 → US3); run **`/speckit-implement`** or execute tasks manually in small PRs with before/after metrics. **`make ci`** must pass before declaring merge-ready.
