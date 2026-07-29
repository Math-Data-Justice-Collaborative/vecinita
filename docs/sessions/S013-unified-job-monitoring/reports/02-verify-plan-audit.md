# 02-verify-plan audit — EV-012 / #116

**Session:** S013-unified-job-monitoring  
**Date:** 2026-07-28  
**Mode:** delta consistency pass

## High confidence (auto-approved — from locked RDs)

| Statement | Source | Verdict |
|-----------|--------|---------|
| Modal owns all long-running admin job lifecycles incl. eval | RD-174, ADR-038 | approve |
| DO Postgres SoT for storage/metrics; Supabase auth-only | RD-175 | approve |
| Admin Jobs list = Modal `GET /jobs` (not FE dual-list merge) | S013-D8 amended | approve |
| SSE + 4s poll fallback | RD-173 | approve |
| Admin-only full job CRUD | RD-176 | approve |
| ChatRAG UI out of scope | hard constraint | approve |
| Playwright T0-ui list→detail required | RD-178 | approve |
| Extend F32/F36; no new Fn | S013-D3 | approve |

## Consistency fixes applied in this pass

| Issue | Fix |
|-------|-----|
| F32 “No cancellation” limitation contradicted RD-176 | Marked superseded by EV-012 |
| ADR-033 still read as current BackgroundTasks SoT | Amendment banner → ADR-038 |
| UJ-044 steps poll-only; F37-only attribution | SSE+fallback; F32/F36 EV-012 |
| ADR-023 “no cancel” | Supersession note |
| Session seed/impact/routing still said “FE federation” | Aligned to Modal-primary |

## Medium confidence — need user verdict

| ID | Statement | Issue |
|----|-----------|-------|
| M1 | Issue #116 v2 “Postgres `jobs` table alignment” | **Verdict A:** Modal = job lifecycle SoT; DO Postgres = metrics/corpus storage only — no Postgres jobs table as runner SoT |
| M2 | “SSE per source” | **Verdict B:** Keep SSE on **both** Modal jobs **and** internal-write (eval progress); Jobs list remains Modal-primary |
| M3 | Eval trigger | **Verdict A:** `POST /internal/v1/eval/runs` creates metrics row + enqueues Modal `job_type=eval` |

## Low confidence / deferred to 04

| ID | Topic |
|----|-------|
| L1 | Exact OpenAPI paths for cancel/retry/delete/events |
| L2 | Whether `modal.Dict` remains JobStore backend vs Modal native queue APIs |
| L3 | Delete semantics: remove Modal job record only vs also soft-delete eval_runs |

## Connectivity

| Check | Result |
|-------|--------|
| UI journeys have Playwright mapping | Pass (UJ-023/044/050 → tests/ui/admin/*) |
| Vitest not sole E2E | Pass |
| Admin-only; no new CORS origins | Pass (RD-175/D15) |

## Gate A→B

**Passed** (2026-07-28) — M1–M3 resolved. Next: **04-tech-plan**.
