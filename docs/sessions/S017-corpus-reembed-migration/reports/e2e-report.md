# E2E Behavior Report — EV-015 / S017 (F41)

> Generated: 2026-07-30  
> Mechanism: mixed (API TestClient + Playwright UI mocks)  
> Journeys tested: UJ-053, UJ-054 (F41 / #167)  
> Branch: `evolve/EV-015-corpus-reembed-migration` @ `a9c7eeb`  
> Mode: evolve / delta_only · parallel with 09-qa

## Summary

| # | Journey | Mechanism | Tier | Status | Notes |
|---|---------|-----------|------|--------|-------|
| 1 | UJ-053 Enqueue corpus rebuild | API (TestClient) + Playwright | T0 | **PASS** | Store-backed; no scrape |
| 2 | UJ-054 Shadow dry-run → promote | API (Postgres) + Playwright | T0 | **PARTIAL** | Playwright PASS; API promote SKIPPED (no local Postgres) |
| — | T1 Integration | pytest integration | T1 | **SKIPPED** | Docker/Postgres unavailable |
| — | T2 Deploy smoke H1–H5 | staging | T2 | **DEFERRED** | 13-deploy-smoke |
| — | T3 Live UJ | staging browser | T3 | **DEFERRED** | 15-service-health |

**Overall (T0 local, F41):** PASS with UJ-054 API promote deferred to CI Postgres.

## Journey → test matrix (F41)

| Journey | API e2e | Vitest | Playwright | T3 |
|---------|---------|--------|------------|-----|
| UJ-053 | `tests/e2e/test_uj053_corpus_rebuild.py` | `test_rebuild_form.test.tsx` | `tests/ui/admin/uj053-corpus-rebuild.spec.ts` | staging @ 13 |
| UJ-054 | `tests/e2e/test_uj054_rebuild_shadow_promote.py` | promote form tests | `tests/ui/admin/uj054-rebuild-promote.spec.ts` | staging @ 12/13 |

## Journey details

### UJ-053: Enqueue corpus rebuild (store-backed)

- **Feature**: F41 / EV-015 #167  
- **Mechanism**: API TestClient (DM ASGI) + Playwright (admin UI mocks)  
- **Steps**:
  1. Enqueue rebuild with mode/force/dry-run — PASS (API + UI)
  2. Runner completes; `job_type=rebuild` on list/detail — PASS (API)
  3. Store-backed path does not scrape — PASS (unit + API)
- **Evidence**: `uv run pytest tests/e2e/test_uj053_corpus_rebuild.py` green; Playwright 1/1 green

### UJ-054: Shadow dry-run → F36 → promote

- **Feature**: F41 / EV-015 #167  
- **Mechanism**: API (internal-write + Postgres) + Playwright  
- **Steps**:
  1. Admin promote UI confirms `rebuild_run_id` — PASS (Playwright)
  2. Shadow dry-run leaves live unchanged until promote — SKIPPED locally (no Postgres); CI
  3. Promote + eval `rebuild_run_id` wire-up — SKIPPED locally; fixtures in e2e/conftest after `a9c7eeb`
  4. F36 against shadow before promote — staging checklist (TC-168) @ 12/13
- **Evidence**: Playwright `uj054-rebuild-promote.spec.ts` PASS; API e2e collection OK with unit suite

## Connectivity columns

| Column | Result |
|--------|--------|
| **T0** | UJ-053 PASS; UJ-054 UI PASS; UJ-054 API deferred to CI |
| **T2 connectivity** | Not run — staging URLs unset |
| **T3 browser** | Not run — deferred to 15 |

## Collection fix (08 follow-up)

`a9c7eeb` removed `pytest_plugins` from UJ-054; fixtures live in `tests/e2e/conftest.py` so CI
`pytest tests/unit … tests/e2e` collection succeeds.

## Findings for 11-verify-impl

| ID | Severity | Finding | Action |
|----|----------|---------|--------|
| E2E-S017-A01 | advisory | UJ-054 API promote not executed locally | Confirm green on CI Postgres or start compose for 11 |
| E2E-S017-A02 | advisory | T2/T3 staging not run | 12/13 / H4–H5 |
| E2E-S017-A03 | advisory | F36-before-promote live gate | Staging runbook @ 13 (TP-S017-07) |
