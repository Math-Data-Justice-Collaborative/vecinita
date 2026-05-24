# Technical decisions log

> **Stage**: 05-verify-tech  
> **Extends**: docs/requirements-decisions.md, docs/product-decisions.md  
> **Last updated**: 2026-05-24

## 05-verify-tech resolutions

| ID | Topic | Decision | Stmt | Source docs updated |
|----|-------|----------|------|---------------------|
| TV-001 | F17 observability | Add **T3.7** shared logging (`VECINITA_LOG_*`, no prompt persistence) | TS-C01, TS-C08 | execution-plan.md |
| TV-002 | F14 eval fixtures | Add **T2.8** (D3 fixtures) + **T14.5** (≥80% benchmark) | TS-C02, TS-C10 | execution-plan.md |
| TV-003 | E2E coverage | Add **T10.6** (UJ-001), **T7.5** (UJ-003), **T10.7** (UJ-005) | TS-C03–C05 | execution-plan.md |
| TV-004 | Data deps table | Correct D1–D4 “Needed By” mappings; D3 → T2.8, T14.5 | TS-C06, TS-C07 | execution-plan.md |
| TV-005 | Task count | **73** tasks (was erroneous 78 / 65 drift) | TS-C20 | execution-plan.md |
| TV-006 | Cost estimate | Pilot **~$42–48/mo** typical; **≤ $50** cap; consolidation if overrun | TS-C11 | execution-plan.md, deployment-integration.md |
| TV-007 | Typechecker | **Pyright** only in CI (test-plan aligned) | TS-C12 | test-plan.md |
| TV-008 | ADR-002 job API | **`/jobs` on Modal ASGI**; DO hosts internal write + ChatRAG | TS-C15 | ADR-002 |
| TV-009 | Sixth deployable | `internal-write-api` documented under ADR-001 + workflow-state | TS-C14, TS-C21 | ADR-001, workflow-state.yaml |
| TV-010 | D4 ingest fixture | Add **T2.9** before ingest tests | TS-C19 | execution-plan.md |
| TV-011 | Modal DB boundary | Add **T13.4** CI grep for `DATABASE_URL` in Modal paths | TS-C13 | execution-plan.md |
| TV-012 | T1.1 scaffold | Explicit `apps/internal-write-api` in layout task | TS-C16 | execution-plan.md |

## EV-001 04-tech-plan resolutions (2026-05-24)

| ID | Topic | Decision | ADR |
|----|-------|----------|-----|
| TV-013 | Ingest tagging order | After chunk, before embed | ADR-015 TP-010 |
| TV-014 | Admin retag | Async job; `job_type=retag` on jobs table | ADR-015 TP-011, TP-012 |
| TV-015 | Tag filter SQL | Union match (doc OR chunk) | ADR-015 TP-013 |
| TV-016 | Tag inference | Same Modal vLLM | ADR-015 TP-014 |
| TV-017 | Browse UI | `/corpus` route + sidebar chips | ADR-015 TP-015 |
| TV-018 | EV-001 task count | **38** new tasks (T15.1–T19.5 incl. T18.7); **111** total | execution-plan.md |
| TV-019 | Data deps D8/D9 | Seed tags verified; tagged corpus pending | data-management-plan.md |
| TV-020 | Connectivity | Extend TC-046 / staging smoke for browse GET | T17.4, T19.2–T19.3 |

## EV-001 05-verify-tech resolutions (2026-05-24)

| ID | Topic | Decision | Stmt | Source docs updated |
|----|-------|----------|------|---------------------|
| TV-021 | T18.6 AC mapping | **AC-T4** (admin tags), not AC-T3 | TS-EV001-01 | execution-plan.md |
| TV-022 | T16.4 vs T18.3 | Ingest batch tag upsert vs admin GET/PATCH split | TS-EV001-02, TS-EV001-03 | execution-plan.md |
| TV-023 | packages/tagging | Approved component in spec + inventory | TS-EV001-10 | spec.md, dependency-inventory.md |
| TV-024 | Batch retag | **Per-document only** in v1 | TS-EV001-09 | feature-list.md |
| TV-025 | Admin PATCH CORS | Add **T18.7** + **TC-049** | TS-EV001-04 | execution-plan.md, test-plan.md |
| TV-026 | H5 browse gate | Add **T19.5**; Phase 5 exit gate includes H5 | TS-EV001-05 | execution-plan.md |
| TV-027 | test-plan connectivity | §Connectivity tiers (H0c/H0i/H4/H5) | TS-EV001-06 | test-plan.md |
| TV-028 | AC-T2 / UJ-010 | **TC-048** Vitest external URL | TS-EV001-07 | test-plan.md, execution-plan.md |
| TV-029 | Traceability tidy | AC-T6 cites, config wiring, RD-030 on T16.2, T19.1 secrets note | TS-EV001-08+ | execution-plan.md, staging-secrets-matrix.md |
| TV-030 | Task count | **38** EV-001 tasks; **111** total | — | execution-plan.md |
| TV-031 | UJ-002 TC mapping | Remove erroneous TC-011 from UJ-002 row | TS-EV001-15 | test-plan.md |

## Deferred / accepted without plan change

| ID | Topic | Rationale |
|----|-------|-----------|
| TV-D01 | AC-C4 load test | Privacy schema covered by T2.1 (TC-031); full load test deferred to post-v1 ops |
| TV-D02 | TDD ordering (T3.4, T9.2, T7.2) | Scaffold/stub tasks; tests follow in same milestone — no reorder |
| TV-D03 | Ingest config explicit tests | Bounds enforced via T6.2/T10.4 wiring to config-spec at implementation |

## Open (implementation-time)

- Exact LlamaIndex / vLLM patch pins (T8.1, T9.2)
- DO App Platform YAML (T14.1)
