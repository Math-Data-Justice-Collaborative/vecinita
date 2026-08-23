# T130.1 — Phase 30 gate TC-252–265 confirmation

> **Session:** S030-corpus-automations · **Cycle:** EV-027 · **Date:** 2026-08-12  
> **Branch:** `evolve/EV-027-corpus-automations` @ `c610056` (+ this task)  
> **Corpus:** [Corpus: feature-list.md §F75–F77] [Spec: docs/test-plan.md §TC-252–265]  
> [Spec: docs/user-journeys.md §UJ-080–082] [Corpus: e2e-coverage]

## Verdict

**PASS** — unit + API e2e + Vitest + Playwright for TC-252–265 / UJ-080–082 are green.

## Suite results

| Layer | Command / scope | Result |
|-------|-----------------|--------|
| Unit (F75–F77) | pytest automation/freshness/finetune modules | **163 passed** |
| API e2e | `tests/e2e/test_uj080_*.py` + uj081 + uj082 | **7 passed** |
| Vitest (DM) | uj080 panel, uj081 freshness UI, uj082 FT UI, automations API | **51 passed** (4 files) |
| Playwright T0-ui | `uj080` / `uj081` / `uj082` admin specs | **6 passed** |

## TC → evidence map

| TC | Journey | Evidence |
|----|---------|----------|
| TC-252–255, TC-264 | UJ-080 | unit catch-up/routes + e2e uj080 + Vitest + Playwright |
| TC-256–259, TC-264 | UJ-081 | unit freshness + e2e uj081 + Vitest + Playwright |
| TC-260–263, TC-265 | UJ-082 | unit FT approve/promote/caps + e2e uj082 + Vitest + Playwright |

## Notes

- Synced stale execution-plan rows **T128.5–T128.7 → completed** (git already had hash-aware re-fetch, freshness UI, UJ-081 e2e/Vitest/Playwright).
- PR [#238](https://github.com/Math-Data-Justice-Collaborative/vecinita/pull/238) remains open (no merge).
- Live H4–H5 / prod enable still deferred to **13**.

## Next

**T130.2** — OpenAPI yaml mirrors for automations/freshness/FT + CORS H0c for new routes.
