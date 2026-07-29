# Phase 19 gate checklist — EV-012 / S013 unified job monitoring

**Session:** S013-unified-job-monitoring  
**Cycle:** EV-012  
**Branch:** `evolve/EV-012-unified-job-monitoring`  
**Date:** 2026-07-29  
**Milestones:** M82–M85  
**PR:** https://github.com/Math-Data-Justice-Collaborative/vecinita/pull/153 (**merged** → `main` @ `6940770`)

## Gate criteria (execution-plan Phase 19)

| Criterion | Status | Evidence |
|-----------|--------|----------|
| All M82–M85 tasks completed (T82.1–T85.5) | PASS | execution-plan M82–M85 tables; HEAD after T85.5 |
| TC-146–TC-151 + TC-124 green at T2; Playwright T0-ui list→detail (RD-178) | PASS | `tests/e2e/test_uj050_job_detail_crud.py`; `test_uj023`/`test_uj044` extensions; `tests/ui/admin/uj050-job-detail.spec.ts` (+ uj023/uj044) |
| AC-J1–AC-J10 satisfied at T2 | PASS (T2) | Vitest M84 + API e2e M85 + Playwright; live T3 deferred to 13-deploy-smoke |
| Modal lifecycle SoT; DO metrics SoT; no Postgres jobs table (M1) | PASS | ADR-038; Modal JobStore + DO eval metrics |
| SSE on Modal jobs + DO eval progress; 4s poll fallback (M2, RD-173) | PASS | `/jobs/events`, eval run events, Vitest poll fallback |
| Eval create → enqueue Modal `job_type=eval` (M3, TP-S013-06) | PASS | M83 enqueue bridge |
| Admin CRUD; soft-delete `eval_runs.deleted_at` on eval job delete | PASS | T82.1 unit + T85.1 e2e; TP-S013-03/05 |
| No new CORS origins / secrets; ChatRAG UI untouched | PASS | T85.4 H0c only; ChatRAG not in EV-012 scope |
| ruff / basedpyright / ESLint clean; pytest + DM Vitest + `make test-ui` green | PASS (scoped) | See 08-verify-build after M85; local Playwright admin project 9/9 |

## Stage pointers

| Stage | Report / artifact |
|-------|-------------------|
| 04-tech-plan | [`reports/04-tech-plan.md`](04-tech-plan.md) |
| 07-build M84 | [`reports/verification-report.md`](verification-report.md) (M84 scoped) |
| 07-build M85 | This file + commits T85.1–T85.5 |
| 08-verify-build | Re-run at M85 / Phase 19 boundary (next) |
| 10-e2e | Pending (routing-plan Lean+build) |
| 13-deploy-smoke | Pending |

## M85 task summary

| Task | Commit | Notes |
|------|--------|-------|
| T85.1 | API e2e UJ-050 TC-146–149 | `tests/e2e/test_uj050_job_detail_crud.py` |
| T85.2 | Extend UJ-023/044 TC-124/150/151 | retag `document_id`, cancelled filter, Modal eval |
| T85.3 | Playwright RD-178 | `uj050-job-detail.spec.ts`, `uj023-jobs-tab.spec.ts`, uj044 update |
| T85.4 | H0c CORS | cancel/retry/delete + `/jobs/events` OPTIONS |
| T85.5 | Phase 19 gate docs | this file |

## Decision

**Phase 19 gate: PASS at T2** — proceed to **08-verify-build** (M85 / phase scope), then **10-e2e** and **13-deploy-smoke** per Lean+build routing. Merge of PR #153 remains blocked until user approval after deploy checks.
