# E2E Behavior Report — EV-017 / S020 (F43–F45)

> Generated: 2026-08-02  
> Mechanism: API (FastAPI TestClient; mocked retrieve/LLM/CE for Batch B)  
> Journeys tested: UJ-057, UJ-058, UJ-059 (primary); UJ-060 (staging ship-path)  
> Branch: `evolve/EV-017-retrieval-batch-b` @ `d9c9f4a`  
> Mode: evolve / delta_only · parallel with 09-qa  
> Features: **F43** cache · **F44** soft language · **F45** CE

## Summary

| # | Journey | Mechanism | Tier | Status | Notes |
|---|---------|-----------|------|--------|-------|
| 1 | UJ-057 Repeat ask hits cache | API TestClient | T0 | **PASS** | 6/6 in `test_uj057_answer_cache.py` (TC-176–179) |
| 2 | UJ-058 Soft language empty-hit | API TestClient | T0 | **PASS** | 3/3 in `test_uj058_soft_language.py` |
| 3 | UJ-059 CE gated ask (mock) | API TestClient | T0 | **PASS** | 2/2 in `test_uj059_ce_rerank.py` |
| 4 | UJ-060 CE ship gate (spike) | Spike harness + staging golden | T0 partial / T2–T3 | **DEFERRED** | [ce-ship-gate.md](./ce-ship-gate.md) template; AC-BB9 / TC-184 |
| — | T1 Integration | `tests/integration/` | T1 | **SKIPPED** | Docker/Postgres unavailable |
| — | T2 Deploy smoke H1–H5 | staging | T2 connectivity | **DEFERRED** | 13-deploy-smoke |
| — | T3 Live UJ / browser | staging | T3 browser | **DEFERRED** | 15-service-health; no new FE |

**Overall T0 (Batch B delta):** **PASS** — **11 passed** (UJ-057–059)  
**UJ-060 / AC-BB9:** **DEFERRED** to staging spike (not a T0 failure)

## Connectivity columns

| Column | Result | Evidence |
|--------|--------|----------|
| **T0** | **PASS** | `uv run pytest tests/e2e/test_uj057_*.py test_uj058_*.py test_uj059_*.py` → 11 passed |
| **T2 connectivity** | **DEFERRED** | Staging H1–H5 not run this stage |
| **T3 browser** | **DEFERRED / N/A** | No new browser UI for F43–F45 |

Mocks passing T0 ≠ production UI/staging connected.

## Journey → test matrix (Batch B)

| Journey | API e2e | Unit (TC) | UI | T3 |
|---------|---------|-----------|----|-----|
| UJ-057 | `tests/e2e/test_uj057_answer_cache.py` | TC-176–179 cache units | — | live warm ask after deploy |
| UJ-058 | `tests/e2e/test_uj058_soft_language.py` | TC-180–181 soft language | — | flag-on staging ask |
| UJ-059 | `tests/e2e/test_uj059_ce_rerank.py` | TC-182–183 CE merge / default off | — | only if CE ship gate passes |
| UJ-060 | harness docs + spike scripts | TC-184 ship floors | — | staging golden + Modal T4 |

### Mapping notes for 11-verify-impl

| ID | Severity | Finding |
|----|----------|---------|
| E2E-S020-A01 | advisory | **UJ-060** has no `tests/e2e/test_uj060_*.py` — intentional (staging spike + ship-gate report). |
| E2E-S020-A02 | ship-path | **AC-BB9 / TC-184** deferred — fill `ce-ship-gate.md` from spike JSON at 12/13. |
| E2E-S020-A03 | advisory | Full `tests/e2e/ -m "e2e and not live"` needs local Docker/Postgres; CI covers after push. |

## Journey details

### UJ-057: Repeat ask hits answer/retrieve cache

- **Feature**: F43 / EV-017  
- **Mechanism**: API TestClient  
- **Result**: **6 passed**  
- **Command**:
  ```bash
  uv run pytest tests/e2e/test_uj057_answer_cache.py -v
  ```

### UJ-058: Soft language fallback on empty same-lang hit

- **Feature**: F44 / EV-017 #162  
- **Mechanism**: API TestClient + empty-hit fixture  
- **Result**: **3 passed**  
- **Command**:
  ```bash
  uv run pytest tests/e2e/test_uj058_soft_language.py -v
  ```

### UJ-059: CE rerank gated ask (flag on after ship)

- **Feature**: F45 / EV-017 #83/#161  
- **Mechanism**: API TestClient + mock CE scorer  
- **Result**: **2 passed** (default off + flag-on mock path)  
- **Command**:
  ```bash
  uv run pytest tests/e2e/test_uj059_ce_rerank.py -v
  ```

### UJ-060: Admin / spike validates F45 CE ship gate

- **Feature**: F45 + F36  
- **Mechanism**: Modal T4 ephemeral spike + eval floors  
- **Result**: **DEFERRED** — runbook + template present; metrics JSON not filled  
- **Artifacts**: [spike-f45-ce-runbook.md](./spike-f45-ce-runbook.md), [ce-ship-gate.md](./ce-ship-gate.md)

## Command evidence

```text
============================== 11 passed in 1.25s ==============================
tests/e2e/test_uj057_answer_cache.py ......
tests/e2e/test_uj058_soft_language.py ...
tests/e2e/test_uj059_ce_rerank.py ..
```

## Overall

| Gate | Status |
|------|--------|
| T0 Batch B (UJ-057–059) | **PASS** |
| Stage 10 complete for delta | **PASS** (with ship-path advisories) |
| Ready for 11-verify-impl | After 09-qa also complete + CI green on #173 |
