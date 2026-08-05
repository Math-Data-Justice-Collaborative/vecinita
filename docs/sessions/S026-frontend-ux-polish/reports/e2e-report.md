# E2E Behavior Report — EV-024 / S026 (F64–F69)

> Generated: 2026-08-04  
> Mechanism: API (FastAPI TestClient) + Vitest + Playwright T0-ui  
> Journeys: **UJ-069**, **UJ-070**, **UJ-073**, **UJ-074** (+ optional 071/072)  
> Main: `c942971` (#207)  
> Mode: evolve / delta_only · parallel with 09-qa  
> Features: **F64–F69**

## Summary

| # | Journey | Mechanism | Tier | Status | Notes |
|---|---------|-----------|------|--------|-------|
| 1 | UJ-069 Wait tips/marketing | Playwright + Vitest | T0-ui | **PASS** | TC-216–217; [t118-1](./t118-1-uj-suite.md) |
| 2 | UJ-070 Energy + car | API e2e + Playwright | T0 | **PASS** | TC-218–220, TC-231 |
| 3 | UJ-073 Anonymous feedback | API e2e + Playwright + privacy | T0 | **PASS** | TC-225–228 |
| 4 | UJ-074 Audit actor email | API e2e + Vitest + privacy | T0 | **PASS** | TC-229–230 |
| — | UJ-071/072 icons/tooltips | Vitest (optional Playwright) | T0 | **PASS** | Covered in M112–M113 Vitest |
| — | T1 Integration | `tests/integration/` | T1 | **PASS** (CI) | Local Docker unavailable |
| — | T2 Deploy smoke H1–H5 | staging | T2 | **DEFERRED** | 13-deploy-smoke |
| — | T3 Live UI | staging | T3 | **DEFERRED** | 13 / 15 |

**Overall T0 (EV-024 delta):** **PASS** — CI python + ui-e2e @ `c942971`; prior local Playwright 3/3 on tip.

## Connectivity columns

| Column | Result | Evidence |
|--------|--------|----------|
| **T0** | **PASS** | UJ-069/070/073/074 + CI ui-e2e |
| **T2 connectivity** | **DEFERRED** | 13-deploy-smoke |
| **T3 browser** | **DEFERRED** | Live staging after deploy |

## Journey → test matrix

| Journey | API e2e | Unit / Vitest | UI E2E | T3 |
|---------|---------|---------------|--------|-----|
| UJ-069 | Vitest + Playwright | TC-216–217 | `uj069-wait-tips.spec.ts` | deferred |
| UJ-070 | `test_uj070_*` (energy) | TC-218–220 | `uj070` Playwright | deferred |
| UJ-073 | feedback e2e + privacy | TC-225–228 | `uj073` Playwright | deferred |
| UJ-074 | `test_uj074_audit_actor_email.py` | TC-229–230 | Admin Vitest | deferred |

## Evidence

| Surface | Run |
|---------|-----|
| CI `ci.yml` @ `c942971` | https://github.com/Math-Data-Justice-Collaborative/vecinita/actions/runs/30962701485 |
| PR CI @ `2b8e8cd` | https://github.com/Math-Data-Justice-Collaborative/vecinita/actions/runs/30962353032 |
| Suite note | [t118-1-uj-suite.md](./t118-1-uj-suite.md) |

## Verdict

**PASS (T0)** — Phase D e2e delta complete. Staging H4–H5 / live secret sync remain for 12/13.
