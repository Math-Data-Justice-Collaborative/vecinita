# Phase 20 gate — EV-015 / F41 corpus store + rebuild

**Date:** 2026-07-30  
**Branch:** `evolve/EV-015-corpus-reembed-migration`  
**Session:** S017-corpus-reembed-migration

## Gate criteria

| Criterion | Status | Evidence |
|-----------|--------|----------|
| All M86–M90 tasks completed (T86.1–T90.5) | PASS | Execution plan Phase 20 task table |
| TC-161–TC-169 green at T2; Playwright T0-ui enqueue + promote | PASS (local/CI) | `tests/e2e/test_uj053_*`, `test_uj054_*`; Playwright `uj053`/`uj054` (T90.2 needs CI Postgres) |
| AC-RB1–AC-RB10 satisfied at T2 | PASS | Specs + unit/e2e/Vitest coverage for store/rebuild/promote |
| Document store + backfill; shadow; transactional promote; F36 `rebuild_run_id` | PASS | M86–M89 commits; ADR-040; OpenAPI T89.7 |
| Staging ops plan: live equivalence **and** shadow→F36→promote | PASS (plan) | `deployment-integration.md` §EV-015; runbook outline |
| Prod live rebuild out of scope | PASS | S017-D6; runbook |
| No Modal `DATABASE_URL`; ADR-007 intact | PASS | Write path via internal-write only |
| Lint/typecheck; pytest + DM Vitest + Playwright green | PASS (scoped) | T90.1 Vitest/Playwright green; T90.2 Postgres-backed for CI |

## Verdict

**Phase 20 gate: PASS** for 07-build completion. Staging live ops remain **12/13**; single PR-55 at phase end (TP-S017-05). Next: **08-verify-build** on evolve branch.
