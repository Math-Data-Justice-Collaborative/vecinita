# Implementation Plan: Faster Docker packaging for Data Management API V1 (Render-aligned)

**Branch**: `002-dm-api-docker-build` | **Date**: 2026-04-18 | **Spec**:
[spec.md](./spec.md)

**Input**: Feature specification from `specs/002-dm-api-docker-build/spec.md`, plus planning
directive: **production image is built on Render**; optimizations MUST follow **Render’s Docker
documentation** and constraints (BuildKit, build context, caching, secrets).

**Note**: This file is produced by `/speckit.plan`. Execution follows
`.specify/templates/plan-template.md`.

## Summary

Reduce **wall-clock time** to produce the **vecinita-data-management-api-v1** image by optimizing
the **`services/scraper`** packaging path that the root [render.yaml](../../render.yaml) uses
(`dockerfilePath: ./services/scraper/Dockerfile`, `dockerContext: ./services/scraper`). Keep
**runtime behavior and contracts** equivalent to today (per spec clarifications). Apply **Render-
compatible** Docker practices: lean **build context** (`.dockerignore`), **layer-friendly**
`Dockerfile` ordering, optional **multi-stage** builds, **pinned base images** where appropriate, and
**no secret-bearing `ARG`s** in the Dockerfile per Render’s guidance. Record **baselines** and post-
change timings per **FR-002** / **FR-008** using the same context path Render uses.

## Technical Context

**Language/Version**: Python 3.11 (base image in current Dockerfile: `python:3.11-slim`).  
**Primary Dependencies**: Packaged via `pyproject.toml` / setuptools; repo also contains
`uv.lock` for local/CI `uv` workflows (evaluate use inside image without changing runtime semantics).  
**Storage**: N/A for build feature (runtime still uses Postgres via `DATABASE_URL` on Render).  
**Testing**: Existing `services/scraper` pytest / quality jobs (`.github/workflows/test.yml`,
`quality-gate.yml`); `make ci` before merge. Optional local `docker build` smoke per [quickstart.md](./quickstart.md).  
**Target Platform**: **Render** Docker web service (`runtime: docker`); local Docker for parity
measurements.  
**Project Type**: Monorepo submodule **`services/scraper`** consumed by Render blueprint at repo
root.  
**Performance Goals**: Meet spec **FR-003** / **FR-004** (≥25% repeat-edit local median, ≥20%
automation median for source-only changes) once baselines are captured.  
**Constraints**: **Render docs**: BuildKit image builds; layer cache; `.dockerignore` reduces
context; env vars may become build `ARG`s—**never** reference `ARG`s that carry secrets; favor
immutable base tags/digests over mutable `latest` for base images to avoid stale public-image cache
surprises. Cannot customize Render’s **build** command—only Dockerfile/context and repo files.  
**Scale/Scope**: Single Dockerfile + context under `services/scraper`; no change to
`vecinita-data-management-api-v1` service contract or env contract unless required for equivalence
documentation (**FR-007**).

## Constitution Check

*GATE: Pre–Phase 0 and re-check post–Phase 1 design. Source: `.specify/memory/constitution.md`.*

| Principle | Status | Notes |
|-----------|--------|-------|
| Community benefit | **Pass** | Faster reliable builds support iteration on data-management paths. |
| Trustworthy retrieval | **Pass** | No retrieval contract change; packaging only. |
| Data stewardship | **Pass** | No ingestion/storage behavior change. |
| Safety & quality | **Pass** | Do not remove tests, scans, or lint; prove equivalence (**FR-006**). |
| Service boundaries | **Pass** | Changes confined to **`services/scraper`** image build; Render
blueprint paths stay the same unless a coordinated one-line path fix is required (unlikely). |

**Re-evaluation (post-design)**: Dockerfile and ignore-file edits stay inside the scraper service
packaging boundary; [contracts/render-docker-build.md](./contracts/render-docker-build.md) records
Render obligations so implementations do not regress security or deployability.

## Project Structure

### Documentation (this feature)

```text
specs/002-dm-api-docker-build/
├── plan.md              # This file
├── research.md          # Phase 0
├── data-model.md        # Phase 1
├── quickstart.md        # Phase 1
├── contracts/           # Phase 1
├── baseline-notes.md    # Baselines + variance + FR-007 inventory (tasks T001–T005)
└── tasks.md             # /speckit.tasks
```

### Source Code (repository root)

```text
services/scraper/
├── Dockerfile           # Primary optimization surface (Render dockerfilePath)
├── pyproject.toml
├── uv.lock              # Present; optional for install strategy in image
├── src/                 # Application source
└── (proposed) .dockerignore  # Shrink build context per Render docs

render.yaml              # dockerfilePath + dockerContext for vecinita-data-management-api-v1
.github/workflows/       # scraper-quality / scraper-ci jobs (reference profile for FR-004)
```

**Structure Decision**: Implement under **`services/scraper/`** only for Dockerfile/context
ignore rules. **Do not** switch production to `services/data-management-api/.../Dockerfile` without
an explicit operator decision—that path exists for other workflows but **Render** intentionally
uses the submodule root per comments in `render.yaml`.

## Complexity Tracking

> No constitution violations requiring justification. Dockerfile layering tradeoffs (e.g.,
> multi-stage vs simplicity) are captured in [research.md](./research.md).

## Phase 0 — Research (`research.md`)

Resolved in [research.md](./research.md): Render Docker constraints, `.dockerignore` strategy,
dependency-install caching patterns compatible with `pip`/`uv` and **FR-007**, and risks (secret
`ARG`s, mutable base tags).

## Phase 1 — Design (`data-model.md`, `contracts/`, `quickstart.md`)

- [data-model.md](./data-model.md): Baseline record fields and measurement profiles.  
- [contracts/render-docker-build.md](./contracts/render-docker-build.md): Non-functional contract for
  Render Docker builds (secrets, context, PORT, health).  
- [quickstart.md](./quickstart.md): Local commands mirroring Render’s context for baselines.

## Execution order (recommended)

1. **Baseline**: Capture repeat-edit and cold timings per **FR-002** (document machine / runner
   profile).  
2. **Context hygiene**: Add `.dockerignore` to exclude caches, virtualenvs, tests, and VCS metadata
   not needed for `pip install .` (validate against Render “context omitted” behavior).  
3. **Dockerfile**: Improve layer caching (e.g., install dependencies before copying full `src` if
   project layout allows; consider multi-stage or `uv`/`pip` wheel cache patterns per research) while
   keeping **Python 3.11** runtime and **CMD** behavior equivalent.  
4. **Verify**: Same tests and image smoke; compare timings; document in feature notes / PR.  
5. **Optional CI**: If a dedicated “docker build” job is added for **FR-004**, match Render’s
   `dockerContext` and document runner cache policy.

## Stop / handoff

- **Branch**: `002-dm-api-docker-build`  
- **Plan path**: `specs/002-dm-api-docker-build/plan.md`  
- **Artifacts**: [research.md](./research.md), [data-model.md](./data-model.md),
  [quickstart.md](./quickstart.md), [contracts/render-docker-build.md](./contracts/render-docker-build.md)  
- **Next command**: `/speckit.implement` (or execute `tasks.md` T001–T015 in order).
