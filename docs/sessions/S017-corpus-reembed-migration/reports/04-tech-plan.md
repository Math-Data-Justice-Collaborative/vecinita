# 04-tech-plan — EV-015 / S017 Corpus document store + rebuild

**Date:** 2026-07-30  
**Mode:** delta (Standard+build — 05/06 skipped)  
**Branch:** `evolve/EV-015-corpus-reembed-migration`

## Summary

Technical plan for #167 / F41: Postgres document store (`body_text` + `document_revisions`),
`job_type=rebuild` with shadow dual-write, transactional promote, F36 via optional
`rebuild_run_id`, Admin enqueue + promote, one-time backfill. Staging exercises **both** a
live same-settings equivalence rebuild **and** full shadow→F36→promote (TP-S017-01/07).

## Locked decisions

| ID | Decision |
|----|----------|
| TP-S017-01 | Build full shadow+promote+F36; ops include live same-settings **and** staging shadow path (amended by TP-S017-07) |
| TP-S017-02 | Dedicated `shadow_chunks` / `shadow_embeddings` + `rebuild_runs` |
| TP-S017-03 | Transactional copy shadow → live on promote |
| TP-S017-04 | Eval enqueue optional `rebuild_run_id` |
| TP-S017-05 | Phase 20 / M86–M90 |
| TP-S017-06 | Promote response `{promoted, rebuild_run_id, chunks_promoted, documents_promoted}`; Admin via corpus API proxy |
| TP-S017-07 | Staging **requires** shadow→F36→promote (+ live equivalence) |
| TP-S017-08 | Backfill via rebuild/job + Admin; prefer rescrape; chunks+ack |
| TP-S017-09 | Minor deps allowed in 07; flag in dependency-inventory |

## Deliverables

| Artifact | Path |
|----------|------|
| Execution plan Phase 20 | `docs/sessions/S000-internal-docs-archive/execution-plan.md` |
| Session roadmap | `docs/sessions/S017-corpus-reembed-migration/roadmap.md` |
| API contract | `docs/api-contract.md` §EV-015 (promote shape locked) |
| Deployment integration | `docs/deployment-integration.md` §EV-015 |
| Data flow | `docs/data-flow.md` ERD + rebuild sequence |
| Decisions | `docs/decisions.md` TP-S017-01–09 |
| ADR-040 | Accepted (product); tech details via TP-S017-* |

## Execution plan shape

| Milestone | Focus | Tasks |
|-----------|-------|-------|
| M86 | Schema: body, revisions, shadow, rebuild_runs | T86.1–T86.4 |
| M87 | Ingest store writes + backfill | T87.1–T87.6 |
| M88 | Rebuild job + shadow dry-run | T88.1–T88.6 |
| M89 | Promote + F36 rebuild_run_id + Admin UI | T89.1–T89.7 |
| M90 | API e2e + Playwright + deploy docs | T90.1–T90.5 |

## Connectivity / UI tests

- Prefer existing CORS origins (Admin → Modal DM + corpus API); T90.4 covers new promote routes
- Playwright T0-ui: `uj053-rebuild-enqueue.spec.ts`, `uj054-rebuild-promote.spec.ts`
- Vitest for enqueue/promote controls (T89.5)
- Existing `make test-ui` / `ui-e2e` CI — no required new deps (TP-S017-09 allows minor if needed)

## Staging ops (build vs run)

| Case | What | When |
|------|------|------|
| Live equivalence | Same params/corpus/chunking as today; write live | Pipeline proof / TC-style smoke |
| Shadow → F36 → promote | `dry_run=true` → eval with `rebuild_run_id` → promote | **Required** staging this cycle (TP-S017-07) |
| Prod | Runbook only | Out of scope for live rebuild |

## Next

User review of Phase 20 → complete 04 → Gate B→C → **07-build** (05/06 skipped).
