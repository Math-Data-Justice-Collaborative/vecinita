# Technical decisions log

> **Stage**: 05-verify-tech  
> **Extends**: docs/requirements-decisions.md, docs/product-decisions.md  
> **Last updated**: 2026-05-19

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

## Deferred / accepted without plan change

| ID | Topic | Rationale |
|----|-------|-----------|
| TV-D01 | AC-C4 load test | Privacy schema covered by T2.1 (TC-031); full load test deferred to post-v1 ops |
| TV-D02 | TDD ordering (T3.4, T9.2, T7.2) | Scaffold/stub tasks; tests follow in same milestone — no reorder |
| TV-D03 | Ingest config explicit tests | Bounds enforced via T6.2/T10.4 wiring to config-spec at implementation |

## Open (implementation-time)

- Exact LlamaIndex / vLLM patch pins (T8.1, T9.2)
- DO App Platform YAML (T14.1)
