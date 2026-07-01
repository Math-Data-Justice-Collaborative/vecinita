# 04-tech-plan — S007 RAG evaluation (EV-008 / #99)

**Session:** S007-rag-eval  
**Evolve cycle:** EV-008 (F36)  
**Date:** 2026-07-01  
**Status:** Complete (baseline + dashboard delta 2026-07-01)

## Intent

Technical planning for GitHub [#99](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/99) —
resolve the tooling blocker, produce ADR + execution-plan Phase 14 tasks for admin RAG evaluation.

**Dashboard scope addition (R68):** See [04-tech-plan-dashboard-delta.md](./04-tech-plan-dashboard-delta.md).

## Tooling decision (unblocks #99)

| Option | Verdict |
|--------|---------|
| **LlamaIndex evaluators + custom harness** | **Selected** (R63, RD-112, ADR-033 §1) |
| Langfuse | Rejected v1 — ops/cost; duplicates admin UI |
| Ragas | Deferred — metric overlap; revisit if judge unstable |
| DeepEval | Deferred — overlaps `tests/eval/` harness |
| Hybrid | Not selected v1 |

**No new runtime dependencies.**

## Technical decisions (TP-S007-01–16)

| ID | Decision |
|----|----------|
| TP-S007-01 | Tooling: LlamaIndex `FaithfulnessEvaluator` + `AnswerRelevancyEvaluator` + custom retrieval/latency/Postgres/admin UI |
| TP-S007-02 | New package `packages/eval` (`vecinita-eval`) — shared by CI harness + internal-write-api |
| TP-S007-03 | Postgres `eval_runs` + `eval_run_items` — no PII columns |
| TP-S007-04 | Runner on **DO internal-write-api** via `BackgroundTasks` — HTTP to Modal embed/LLM; no new Modal app v1 |
| TP-S007-05 | Corpus profiles: `fixture` (default) \| `staging` via POST body |
| TP-S007-06 | Access: **admin-only**; viewer → 403 on all eval routes (RD-110) |
| TP-S007-07 | API per `api-contract.md` §EV-008; schemas in `vecinita_shared_schemas` |
| TP-S007-08 | Admin UI `/evaluation` + `admin.nav.evaluation` i18n |
| TP-S007-09 | `GroundednessScorer` protocol — LlamaIndex default; #84 adapter when landed |
| TP-S007-10 | Cost: ~42 LLM calls/run; &lt;$0.50 at pilot; CI mocks judge |
| TP-S007-11 | CORS: extend preflight test for `POST /internal/v1/eval/runs` |
| TP-S007-12 | Branch `feat/S007-rag-eval`, PR-50 |
| TP-S007-13 | Redeploy: migration → internal-write-api → admin FE → CI |
| TP-S007-14 | Modal tiers T0–T2 merge-blocking; T3 live eval at deploy-smoke |
| TP-S007-15 | Golden fixture D3 verified in repo (14 locale rows) |
| TP-S007-16 | **No new deps** |

## Execution plan delta

**Phase 14** appended — 5 milestones, 24 tasks (T59.1–T63.4):

| Milestone | Focus |
|-----------|-------|
| M59 | Schema + `packages/eval` scaffold |
| M60 | Harness — LlamaIndex judges + runner |
| M61 | internal-write-api eval routes |
| M62 | Admin Evaluation tab |
| M63 | Deploy docs + gate |

## Artifacts produced

| Artifact | Path |
|----------|------|
| ADR | `docs/adr/ADR-033-ev008-rag-evaluation-implementation.md` |
| Execution plan | `docs/execution-plan.md` — Phase 14, Current State, PR-50 |
| Dependency inventory | `docs/dependency-inventory.md` — §EV-008 evaluation |
| Staging secrets | `docs/staging-secrets-matrix.md` — `VECINITA_EVAL_*` |
| Decisions log | `docs/decisions.md` — TP-S007-01–16 |

## Handoff

**Baseline (M59–M63):** Delivered on `feat/S007-rag-eval` / PR-113.

**Dashboard delta (M64):** 04-tech-plan complete — **ADR-034**, TP-S007-17–25.  
**Next stage:** 07-build — start **T64.1** (Vitest TC-117 red).

**Coordinate:** #84 groundedness adapter when verifier lands; #83/#94 improve golden-set meaningfulness post-v1.
