# Implementation Plan: Gateway live reliability, schema coverage, and Render-owned persistence

**Branch**: `001-gateway-live-schema` | **Date**: 2026-04-18 | **Spec**:
[spec.md](./spec.md)

**Input**: Feature specification from `specs/001-gateway-live-schema/spec.md`, plus planning
directive: **database access only on Render-hosted services**; **model, embedding, and scraper**
compute paths must **not** open Postgres—they return **payloads** to Render, which performs **all**
persistence.

**Note**: This file is produced by `/speckit.plan`. Execution follows
`.specify/templates/plan-template.md`.

## Summary

Deliver **(1)** stable live gateway behavior and **100%** TraceCov/schema dimensions for the
standard Schemathesis gateway pass per `spec.md` clarifications (**gateway Render env** scope for
mandatory connectivity fixes; **full OpenAPI `responses`** for every included operation unless
waived). In parallel, establish an **architectural boundary**: **Postgres and all durable writes**
are owned by **Render services** (gateway and/or agent as deployed on Render). **Modal** (or other
non-Render) **model**, **embedding**, and **scraper** functions **must not** hold or use database
DSNs; they **return structured payloads** to Render callers, which **commit** to the database.
This removes unreachable internal DB hostnames from Modal runtimes and aligns with the
constitution’s data-stewardship and service-boundary principles.

## Technical Context

**Language/Version**: Python 3.10 (backend), TypeScript (frontend; unchanged for this feature).  
**Primary Dependencies**: FastAPI, LangGraph (agent), Modal SDK (invoke), PostgreSQL (psycopg /
SQL on Render only), Schemathesis + TraceCov for contract gates.  
**Storage**: PostgreSQL; **connections only from Render-deployed** gateway/agent processes (not
from Modal workers after refactor).  
**Testing**: `pytest` integration + `make test-schemathesis-cli` / `make test-schemathesis-gateway`;
offline mocks in `backend/tests/integration/test_api_schema_schemathesis.py` patterns.  
**Target Platform**: Render (gateway, agent, DB) + Modal (stateless or payload-returning compute).  
**Project Type**: Multi-service monorepo (`backend/`, `frontend/`, `services/*` as applicable).  
**Performance Goals**: Modal round-trips remain bounded; batch persistence on Render should avoid
timeout regressions on large scrape batches (target: document p95 budget in tasks).  
**Constraints**: Spec clarifications **B** (mandatory env changes **gateway Render** only for
connectivity); **FR-006** full `responses` OpenAPI for included ops; new directive adds **no DB
from Modal** for model/embedding/scraper—**migration** must preserve API contracts or version them.  
**Scale/Scope**: All gateway OpenAPI operations selected by live script; Modal scraper/model/embed
code paths that currently import DB clients or env DSNs.

## Constitution Check

*GATE: Pre–Phase 0 and re-check post–Phase 1 design. Source: `.specify/memory/constitution.md`.*

| Principle | Status | Notes |
|-----------|--------|-------|
| Community benefit | **Pass** | Reliable ingestion and honest contracts support public corpus use. |
| Trustworthy retrieval | **Pass** | Documented errors/responses; no silent DB failures masked as 500. |
| Data stewardship | **Pass** | Centralizing writes on Render improves auditability and DSN hygiene. |
| Safety & quality | **Pass** | Contract tests + migration tests required; OpenAPI stays truthful. |
| Service boundaries | **Pass with complexity** | New boundary between **compute (Modal)** and
**persistence (Render)**; justified in **Complexity Tracking** below. |

**Re-evaluation (post-design)**: The Modal→Render payload split **increases** gateway/agent
responsibilities but **clarifies** ownership; acceptable if contracts and idempotency are defined
(`contracts/`).

## Project Structure

### Documentation (this feature)

```text
specs/001-gateway-live-schema/
├── plan.md           # This file
├── research.md       # Phase 0
├── data-model.md     # Phase 1
├── quickstart.md     # Phase 1
├── contracts/        # Phase 1
└── tasks.md          # /speckit.tasks (not created here)
```

### Source Code (repository root)

```text
backend/src/api/              # Gateway: OpenAPI responses, orchestration, new persist endpoints if needed
backend/src/agent/            # Agent: DB tools remain Render-only; no Modal DB
backend/src/services/modal/   # Invokers; payloads in/out without DB
services/embedding-modal/     # Remove direct DB; return vectors for Render to store (if applicable)
services/model-modal/         # No Postgres; return generation payloads only
services/scraper/             # Modal scraper: return chunks/job status; Render gateway/agent persists
backend/tests/                # Integration + schemathesis
backend/scripts/              # run_schemathesis_live.sh, hooks
docs/deployment/              # Render env contract updates, operator runbook (SC-004)
```

**Structure Decision**: Primary code changes in **`backend/`** (gateway orchestration, OpenAPI)
and **`services/*`** Modal apps (strip DB, adjust return contracts). **Render** remains the only
runtime that opens `DATABASE_URL` / `MODAL_DATABASE_URL` is **removed** from Modal secrets where
present.

## Complexity Tracking

| Violation / tension | Why needed | Simpler alternative rejected because |
|---------------------|------------|-------------------------------------|
| Extra gateway/agent round-trips (Modal → HTTP → Render → DB) | User directive: **no DB** on
model/embed/scraper compute | Keeping DB in Modal fails DNS/reachability and violates stated
architecture |
| Larger payloads over HTTP | Batch writes must be explicit | Streaming partial DB writes from
Modal are exactly what we are removing |

## Phase 0 — Research (`research.md`)

Resolved in [research.md](./research.md): Render-vs-Modal responsibility matrix, DSN removal
checklist, idempotency keys for batch inserts, and compatibility with existing `invoke_modal_*`
gateway routes.

## Phase 1 — Design (`data-model.md`, `contracts/`, `quickstart.md`)

- [data-model.md](./data-model.md): Payload DTOs and persistence entities on the Render side.  
- [contracts/gateway-persistence-boundary.md](./contracts/gateway-persistence-boundary.md):
  Sequence and HTTP/internal contracts for “Modal returns → Render persists”.  
- [quickstart.md](./quickstart.md): Local and Render env expectations after the split.

## Execution order (recommended)

1. **Operational / contract (spec clarifications B + A)**: Gateway Render env audit; OpenAPI
   `responses` (FR-006); re-run live Schemathesis until gate green or exception register filed.  
2. **Persistence boundary (this plan directive)**: Inventory Modal + services for `psycopg`,
   `DATABASE_URL`, `MODAL_DATABASE_URL`; refactor to payload-return; add Render-side persist
   handlers; feature-flag or dual-write window if needed.  
3. **Documentation**: Operator runbook (SC-004) + `docs/deployment` env contract updates.

## Stop / handoff

- **Branch**: `001-gateway-live-schema`  
- **Plan path**: `specs/001-gateway-live-schema/plan.md`  
- **Artifacts**: `research.md`, `data-model.md`, `quickstart.md`,
  `contracts/gateway-persistence-boundary.md`  
- **Next command**: `/speckit.tasks` to break work into ordered tasks.
