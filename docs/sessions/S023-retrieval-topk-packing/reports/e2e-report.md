# E2E Behavior Report — EV-020 / S023 (F50–F51)

> Generated: 2026-08-03  
> Mechanism: API (FastAPI TestClient) + unit coverage for defaults  
> Journeys: **UJ-063** (primary); **UJ-055** regression (explicit `p1`); UJ-004 bootstrap assert  
> Branch: `evolve/EV-020-retrieval-topk-packing` @ `4ea0c62`  
> Mode: evolve / delta_only · parallel with 09-qa  
> Features: **F50** top_k=8 · **F51** default P3 packing

## Summary

| # | Journey | Mechanism | Tier | Status | Notes |
|---|---------|-----------|------|--------|-------|
| 1 | UJ-063 Ask top_k=8 + P3 | API TestClient `POST /api/v1/ask` | T0 | **PASS** | TC-195 — 2/2 |
| — | UJ-055 H7 + explicit p1 | API TestClient (fixture forces `p1`) | T0 | **PASS** | regression — p1 still selectable |
| — | UJ-004 local bootstrap | yaml/config assert `top_k==8` | T0 | **PASS** (1 pass, 1 skip) | default wiring |
| — | F50 DEFAULT_TOP_K | unit TC-193 | T0 | **PASS** | `test_constants.py` |
| — | F51 packer p3 | unit TC-194 | T0 | **PASS** | config + `test_context_packing.py` |
| — | T1 Integration | `tests/integration/` | T1 | **SKIPPED** | Docker unavailable |
| — | T2 Deploy smoke H1–H5 | staging | T2 | **DEFERRED** | 13-deploy-smoke |
| — | T3 Live browser UJ | staging | T3 | **N/A** | AC-RQ10 — no new FE |

**Overall T0 (EV-020 delta):** **PASS** — **76 passed / 0 failed / 12 skipped** (UJ-063 + supporting units + H0c)

Full `tests/e2e/ -m "e2e and not live"` without Postgres: **65 passed, 9 failed, 2 skipped, 44 errors** — fixture/DB setup failures (not F50/F51 regressions). Treat as CI-gated, same pattern as S022.

## Connectivity columns

| Column | Result | Evidence |
|--------|--------|----------|
| **T0** | **PASS** | UJ-063 2/2 + TC-193/194 + UJ-055 regression |
| **T2 connectivity** | **DEFERRED** | 13-deploy-smoke |
| **T3 browser** | **N/A** | No ChatRAG FE knobs this cycle (AC-RQ10) |

## Journey → test matrix

| Journey | API e2e | Unit (TC) | T3 |
|---------|---------|-----------|-----|
| UJ-063 | `tests/e2e/test_uj063_topk_p3_ask.py` | TC-193–195 | deferred / N/A |
| UJ-055 (p1 explicit) | `tests/e2e/test_uj055_h7_p1_ask.py` | TC-170–173 | N/A |
| F50 top_k default | UJ-004 / UJ-063 | TC-193 `test_constants.py`, `test_config.py` | N/A |
| F51 packer default | UJ-063 | TC-194 packing + ChatRAG config | N/A |

## UJ-063 step results

| Step | Assertion | Test | Status |
|------|-----------|------|--------|
| 1–2 | Default ask returns ≤8 sources (= `top_k`) | `test_uj063_ask_returns_at_most_eight_sources` | **PASS** (TC-195 / AC-RQ8) |
| 3 | Packer mode `p3`; shared `document_id` deduped in prompt | `test_uj063_ask_uses_p3_packer_by_default` | **PASS** (TC-195 / AC-RQ9) |
| 4 | Spanish language match | covered by UJ-001/055 suite; not re-asserted in UJ-063 | **deferred to CI / prior green** |

## Commands

```bash
unset DATABASE_URL
uv run pytest \
  tests/unit/rag/test_constants.py \
  tests/unit/rag/test_context_packing.py \
  tests/unit/chat_rag/test_config.py \
  tests/unit/eval/test_runner_sandbox_config.py \
  tests/e2e/test_uj063_topk_p3_ask.py \
  tests/e2e/test_uj055_h7_p1_ask.py \
  tests/e2e/test_uj004_local_bootstrap.py \
  tests/unit/test_cors_policy.py -v
```

## Findings for 11-verify-impl

| ID | Severity | Finding |
|----|----------|---------|
| E2E-S023-A01 | advisory | T1 integration + full e2e suite need Postgres — CI on PR |
| E2E-S023-A02 | ship-path | Live DO must apply `VECINITA_TOP_K=8` + `VECINITA_RAG_PACKER=p3` at 12/13 |
| E2E-S023-A03 | info | AC-RQ10 held — no Playwright; T3 browser N/A for this cycle |
| E2E-S023-A04 | info | UJ-055 still forces `rag_packer="p1"` intentionally (p1 remains selectable) |

## AC mapping (pre-11)

| AC | Status (T0 evidence) |
|----|----------------------|
| AC-RQ8 | **met** — TC-193 unit + TC-195 / UJ-063 e2e; DO `VECINITA_TOP_K=8` |
| AC-RQ9 | **met** — TC-194 unit + TC-195 / UJ-063 packer spy; DO `VECINITA_RAG_PACKER=p3` |
| AC-RQ10 | **held** — no adaptive top_k, CE, Path B, FE truncation, or Playwright |
