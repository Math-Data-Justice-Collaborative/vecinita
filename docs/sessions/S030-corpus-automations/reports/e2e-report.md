# E2E Behavior Report — EV-027 / S030 (F75–F77)

> Generated: 2026-08-12  
> Mechanism: mixed — API (FastAPI TestClient) + Playwright T0-ui (DM admin)  
> Journeys: **UJ-080**, **UJ-081**, **UJ-082**  
> Branch: `evolve/EV-027-corpus-automations` @ `3466b2b`  
> Mode: evolve / delta · after Gate C→D (S030-D55) + **09-qa**  
> Features: **F75** catch-up automations · **F76** freshness · **F77** LoRA FT + human promote  

[Corpus: feature-list.md §F75] [Corpus: feature-list.md §F76] [Corpus: feature-list.md §F77]  
[Spec: docs/user-journeys.md §UJ-080] [Spec: docs/user-journeys.md §UJ-081] [Spec: docs/user-journeys.md §UJ-082]  
[Spec: docs/test-plan.md §TC-252–265]  
[Spec: docs/adr/ADR-052-corpus-automation-orchestration.md]  
[Spec: docs/adr/ADR-053-modal-lora-finetune.md]  
[Spec: docs/sessions/S030-corpus-automations/reports/qa-report.md]

## Summary

| # | Journey | Mechanism | Tier | Status | Notes |
|---|---------|-----------|------|--------|-------|
| 1 | UJ-080 Enable automations + run history | API e2e + Playwright | T0 / T0-ui | **PASS** | TC-252, TC-255 · API 1/1; UI 2/2 |
| 2 | UJ-081 Refresh stale / freshness | API e2e + Playwright | T0 / T0-ui | **PASS** | TC-256–259, TC-264 · API 2/2; UI 2/2 |
| 3 | UJ-082 Approve FT + human promote | API e2e + Playwright | T0 / T0-ui | **PASS** | TC-260–263, TC-265 · API 4/4; UI 2/2 |
| — | Full T0 suite regression | `tests/e2e` not live | T0 | **PASS** | **145** passed |
| — | T1 Integration | `tests/integration/` | T1 | **CARRY** | QA-S030-001 (alembic tip) → **11** |
| — | T2 Deploy smoke H1–H5 | staging | T2 | **DEFERRED** | 13-deploy-smoke; QA-S030-002 |
| — | T3 Live UJ / GPU train | staging/prod | T3 | **DEFERRED** | 13 / 15; prod enable/promote AskQuestion |

**Overall T0 (EV-027 delta):** **PASS** — UJ-080–082 API + Playwright green; full local e2e suite green.

## Connectivity columns

| Column | Result | Evidence |
|--------|--------|----------|
| **T0** | **PASS** | pytest UJ-080–082 **7 passed**; full `tests/e2e -m "e2e and not live"` **145 passed** |
| **T0-ui** | **PASS** | Playwright UJ-080–082 **6 passed** (re-run this stage); 09 suite had 52 passed |
| **T2 connectivity** | **DEFERRED** | QA-S030-002 → 13 H4–H5 (staging FE URLs unset) |
| **T3 browser** | **DEFERRED** | Live UJ after H4–H5; mocks ≠ production CORS/`VITE_*` |

## Journey → test matrix

| Journey | Module | TCs | T0 | T3 |
|---------|--------|-----|----|-----|
| UJ-080 | `tests/e2e/test_uj080_automations.py` + `tests/ui/admin/uj080-automations.spec.ts` | TC-252–255, TC-264 | **PASS** | Live Automations @ 13 |
| UJ-081 | `tests/e2e/test_uj081_freshness.py` + `tests/ui/admin/uj081-freshness.spec.ts` | TC-256–259, TC-264 | **PASS** | Live freshness @ 13 |
| UJ-082 | `tests/e2e/test_uj082_finetune.py` + `tests/ui/admin/uj082-finetune.spec.ts` | TC-260–263, TC-265 | **PASS** | Live Modal train @ 15 (opt) |

## UJ-080 step results (API e2e)

| Step | Assertion | Evidence | Status |
|------|-----------|----------|--------|
| 1 | GET automations config (kill-switch / max concurrent) | TC-252 · `/internal/v1/automations/config` | **PASS** |
| 2 | PATCH enable → `enabled: true` | TC-252 | **PASS** |
| 3 | GET run history includes seeded `automation_catchup` completed run | TC-255 | **PASS** |
| 4 | PATCH disable → `enabled: false` (confirm GET) | TC-252 | **PASS** |

```text
uv run pytest tests/e2e/test_uj080_automations.py -v
# 1 passed
```

### UJ-080 T0-ui (Playwright)

| Step | Assertion | Status |
|------|-----------|--------|
| Nav → Automations panel with enable + history | **PASS** |
| Disable PATCHes config and shows disabled (TC-252) | **PASS** |

## UJ-081 step results (API e2e)

| Step | Assertion | Evidence | Status |
|------|-----------|----------|--------|
| 1 | Stale list (`stale=true`) shows doc older than 30d | TC-256, TC-258 | **PASS** |
| 2 | `refresh_enabled=false` → Refresh now **409**; no enqueue | TC-259 | **PASS** |
| 3 | Re-enable + Refresh now enqueues freshness job (`force=true`) | TC-259 | **PASS** |
| 4 | mark-checked bumps `last_checked_at`; drops from stale list | TC-257 | **PASS** |
| 5 | Freshness helper does not enqueue F75 catch-up | TC-264 / AC-FR5 | **PASS** |

```text
uv run pytest tests/e2e/test_uj081_freshness.py -v
# 2 passed
```

### UJ-081 T0-ui (Playwright)

| Step | Assertion | Status |
|------|-----------|--------|
| Stale badge + last_checked; Refresh now queues job | **PASS** |
| Disable refresh_enabled PATCHes; Refresh now disabled | **PASS** |

## UJ-082 step results (API e2e)

| Step | Assertion | Evidence | Status |
|------|-----------|----------|--------|
| 1 | Create `finetune_train` → pending, not approved | TC-260 | **PASS** |
| 2 | Approve → train completes; adapter metrics | TC-260 | **PASS** |
| 3 | Eval report base vs adapter; human-judgment promote | TC-261–262 | **PASS** |
| 4 | Promote pins adapter; rollback clears to base | TC-262, TC-265 | **PASS** |
| 5 | Kill-switch / daily cap block train after approve | TC-263 | **PASS** |
| 6 | Create without approve does not start GPU | TC-260 | **PASS** |

```text
uv run pytest tests/e2e/test_uj082_finetune.py -v
# 4 passed
```

### UJ-082 T0-ui (Playwright)

| Step | Assertion | Status |
|------|-----------|--------|
| Nav → Fine-tune; request train + approve (TC-260) | **PASS** |
| Eval → human-confirm promote → rollback (TC-261/262/265) | **PASS** |

## Commands (combined delta)

```bash
uv run pytest tests/e2e/test_uj080_automations.py \
  tests/e2e/test_uj081_freshness.py \
  tests/e2e/test_uj082_finetune.py -v
# 7 passed in 0.53s

uv run pytest tests/e2e/ -m "e2e and not live" -q
# 145 passed

npx playwright test \
  tests/ui/admin/uj080-automations.spec.ts \
  tests/ui/admin/uj081-freshness.spec.ts \
  tests/ui/admin/uj082-finetune.spec.ts --reporter=line
# 6 passed (2.4s)
```

## Carry-forward to 11-verify-impl

| ID | Item | Source |
|----|------|--------|
| QA-S030-001 | Alembic tip assert still expects `20260806_0014`; head is `20260812_0016` | 09-qa FAIL (H0i) |
| QA-S030-002 | H4–H5 staging FE URLs unset | 09 advisory → 13 |
| QA-S030-005 | Prod automation enable / FT promote AskQuestion | 09 → 13 |

## Overall

**PASS** (T0 / T0-ui for F75–F77). T1 integration tip-pin failure remains from 09 and is **out of scope for code fix in this report-only stage** — dispose at **11-verify-impl**. PR [#238](https://github.com/Math-Data-Justice-Collaborative/vecinita/pull/238) stays open.
