# E2E Behavior Report — EV-018 / S021 (F46 + F45)

> Generated: 2026-08-02  
> Mechanism: API (FastAPI TestClient) + staging CE spike harness  
> Journeys: UJ-061 (primary F46); UJ-059 (F45 default-off); UJ-060 (ship gate)  
> Branch: `evolve/EV-018-retrieval-follow-on` @ `1b46507`  
> Mode: evolve / delta_only · parallel with 09-qa  
> Features: **F46** non-empty retrieve · **F45** CE re-gate

## Summary

| # | Journey | Mechanism | Tier | Status | Notes |
|---|---------|-----------|------|--------|-------|
| 1 | UJ-061 Non-empty retrieve / ask sources | API TestClient | T0 | **PASS*** | TC-186 PASS; TC-185 skipped locally (S021-D23); staging AC-FO1 via Path B |
| 2 | UJ-059 CE gated ask (mock) | API TestClient | T0 | **PASS** | 2/2 including TC-183 default-off |
| 3 | UJ-060 CE ship gate | Spike harness + staging golden | T2/T3 ops | **PASS** | `ship_gate_pass=true` (CE+P1 0.778 / 0.938) |
| — | BUG-2026-08-02 guard | unit/bug | T0 | **PASS** | 2 + corpus_db_guard 6 |
| — | T1 Integration | `tests/integration/` | T1 | **SKIPPED** | Docker unavailable |
| — | T2 Deploy smoke H1–H5 | staging | T2 | **DEFERRED** | 13-deploy-smoke |
| — | T3 Live browser UJ | staging | T3 | **DEFERRED** | no new FE |

\* Local T0 fixture TC-185 waived (CI-gated); staging pools evidenced by Path B + T100.1 (`pool=20` × 18).

**Overall T0 (EV-018 delta):** **PASS** — **11 passed / 1 skipped**  
**UJ-060 / AC-BB9:** **PASS** (staging spike)

## Connectivity columns

| Column | Result | Evidence |
|--------|--------|----------|
| **T0** | **PASS** | UJ-061/059 + bug/guard suite |
| **T2 connectivity** | **DEFERRED** | 13-deploy-smoke |
| **T3 browser** | **N/A** | No new browser UI |

## Journey → test matrix

| Journey | API e2e / harness | Unit (TC) | T3 |
|---------|-------------------|-----------|-----|
| UJ-061 | `tests/e2e/test_uj061_retrieve_nonempty.py` | TC-185/186 | staging golden retrieve |
| UJ-059 | `tests/e2e/test_uj059_ce_rerank.py` | TC-182–183 | only after CE flag Path A |
| UJ-060 | `spike_f45_ce_ship_gate.py` + [ce-ship-gate.md](./ce-ship-gate.md) | TC-184 | done at T100.1 |

## Commands

```bash
unset DATABASE_URL
uv run pytest \
  tests/e2e/test_uj061_retrieve_nonempty.py \
  tests/e2e/test_uj059_ce_rerank.py \
  tests/bugs/test_bug_2026_08_02_staging_basis_vector_wipe.py \
  tests/unit/test_corpus_db_guard.py -v
# Staging CE (already run T100.1):
# uv run python docs/sessions/S020-retrieval-batch-b/scripts/spike_f45_ce_ship_gate.py
```

## Findings for 11-verify-impl

| ID | Severity | Finding |
|----|----------|---------|
| E2E-S021-A01 | advisory | TC-185 local skip — CI + staging Path B evidence |
| E2E-S021-A02 | ship-path | CE flag remains default-off despite AC-BB9 PASS (AC-FO4) |
