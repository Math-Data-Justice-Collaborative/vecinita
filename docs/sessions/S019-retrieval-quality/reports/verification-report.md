# 08-verify-build — Phase 21 (M91–M93 / F42)

> **Session:** S019 · **Cycle:** EV-016 · **Branch:** `evolve/EV-016-retrieval-quality`  
> **Date:** 2026-08-01 · **HEAD:** post-`58c79da` (+ lint fix)

## Scope

Delta verify for F42 H7+P1 (packages/rag packing + multi-query, ChatRAG wire-up, F36 sandbox, UJ-055, ISS-008 fixture path).

## Results

| Check | Result |
|-------|--------|
| Ruff (F42 modules + tests) | **PASS** |
| Ruff format (F42 production) | **PASS** |
| basedpyright (F42 production) | **PASS** (0 errors) |
| Unit: packing / H7 / ChatRAG config+service | **PASS** |
| Unit: eval sandbox F42 packing + truncation | **PASS** |
| Unit: staging ES coverage + fixture path | **PASS** |
| E2E: `test_uj055_h7_p1_ask.py` | **PASS** |
| CORS unit (`test_cors_policy.py`) | **PASS** (env-skipped cases noted as `s`) |
| Full `test_eval_service.py` suite | **SKIPPED locally** — requires Postgres/Docker (daemon unavailable); ISS-008 path unit tests ran green |

## Connectivity (stage 08)

- CORS unit policy tests exercised (pass / skip as marked).
- Integration DB suite not run locally (Docker unavailable).
- Live connectivity artifacts remain for 12/13.

## Gate

Phase 21 code verify **PASS** at T2 for TC-170–174 / UJ-055.  
AC-RQ6 (Hy1 staging floors) deferred to deploy path after ISS-008 write-api deploy — see `hy1-ship-gate.md`.

## Out of scope (left uncommitted)

- `infra/modal/llm_app.py`, `llm_playground_app.py`
- `playground_hf_registry` + related tests
- `scripts/deploy/_tmp_proxy_key_check.py`
- `tests/unit/modal/test_llm_engine_awq_kwargs.py`
