# 07-build — S007 RAG evaluation (EV-008 / #99)

**Session:** S007-rag-eval  
**Date:** 2026-07-01  
**Stage:** 07-build  
**Branch:** `feat/S007-rag-eval`

## Summary

Implemented F36 admin RAG evaluation per ADR-033 across M59–M63:

| Milestone | Deliverables |
|-----------|--------------|
| M59 | `eval_runs` / `eval_run_items` migration, `packages/eval` scaffold, privacy + retrieval tests |
| M60 | Golden-set runner, LlamaIndex judge wiring, groundedness protocol, TC-112/113 |
| M61 | `vecinita_shared_schemas` eval models, internal-write-api routes + BackgroundTasks runner, CORS preflight, TC-114/115 |
| M62 | Admin `/evaluation` tab, bilingual nav, Vitest TC-116 |
| M63 | OpenAPI eval routes, AC-E12–E16 marked complete, secrets matrix already documented |

## Tooling decision

**LlamaIndex evaluators + custom harness** (ADR-033) — no new runtime dependencies.

## Verification (local)

- `pytest tests/privacy/test_eval_tables.py tests/eval tests/integration/test_eval_routes.py tests/e2e/test_uj039_eval_run_trigger.py` — pass
- Vitest `test_evaluation_page.test.tsx` — pass
- Alembic `20260701_0005` applied locally

## Next

- **08-verify-build** at Phase 14 scope
- **PR-50** `feat/S007-rag-eval` → `main` (closes #99)
- **13-deploy-smoke**: informational live staging eval run (T3)
