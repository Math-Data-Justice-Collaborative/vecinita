# Verification report — M115 (F65 / #93)

**Session:** S026-frontend-ux-polish  
**Cycle:** EV-024  
**Stage:** 08-verify-build (milestone boundary)  
**Date:** 2026-08-04  
**Branch:** `evolve/EV-024-frontend-ux-polish`  
**Head:** `d93b78a`

## Scope

M115 — Ask energy estimate: backend `energy_estimate` on `/ask` + stream `done`
(`tdp_util_walltime_v1`); FE chip (Wh / gCO₂e), car-distance line, advisory, use
guide (EN/ES); OpenAPI `EnergyEstimate`; Vitest + Playwright UJ-070 / TC-218–220,
TC-231.

## Checks

| Check | Result | Notes |
|-------|--------|-------|
| Unit `tests/unit/chat_rag/test_energy_estimate.py` | **PASS** | Formula + knobs |
| ChatRAG Vitest (`EnergyEstimatePanel`, `test_uj070_energy`) | **PASS** | Node 24 (Node 26 localStorage opaque-origin break) |
| Playwright `tests/ui/chat/uj070-energy.spec.ts` | **PASS** | Chip, car line, advisory, use guide |
| API e2e `tests/e2e/test_uj070_energy_estimate.py` | **CI** | Local Colima Postgres volume chmod denied; Desktop unable to start — CI compose runs TC-218–219 |
| Ruff on e2e + energy surfaces | **PASS** | TC002/PT018/RUF002 fixed in e2e |
| ChatRAG FE lint | **PASS** | |
| Modal GPU smoke | **SKIPPED** | Heuristic only; no GPU budget ask |

## Connectivity artifacts

| Artifact | Present |
|----------|---------|
| `tests/smoke/test_staging_connectivity.py` | Yes (unchanged) |
| CORS / H0c | Unchanged this milestone |

## Auto-corrections

None beyond e2e lint fixes above.

## Verdict

**PASS** — open minor PR for #93 after push; merge needs explicit approval.

Next after PR open: **M116** F68 feedback (#186) on same evolve branch (unless user pauses).
