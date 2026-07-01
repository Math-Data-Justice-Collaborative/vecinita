# 01-requirements — S007 RAG evaluation (EV-008 / #99)

**Session:** S007-rag-eval  
**Evolve cycle:** EV-008 (F36)  
**Date:** 2026-07-01  
**Status:** Complete

## Intent

Delta requirements interview for GitHub [#99](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/99) —
admin Model / RAG Evaluation tab, expanded bilingual golden set, eval runner with metrics + history.
Unblocks issue tooling blocker via **R63** (LlamaIndex + custom harness, decided in 00-context).

## Document manifest

| Document | Action |
|----------|--------|
| feature-list.md | Delta — **F36** |
| user-journeys.md | Delta — UJ-039, UJ-040 |
| test-plan.md | Delta — TC-111–TC-116 |
| acceptance-criteria.md | Delta — AC-E12–AC-E16 |
| api-contract.md | Delta — §EV-008 eval routes |
| config-spec.md | Delta — `VECINITA_EVAL_*` thresholds |
| eval-golden-set.md | **New** — curation runbook |
| deployment-integration.md | Delta — §EV-008 redeploy order |
| data/fixtures/eval/qa_pairs.json | Expanded — 10 cases, 14 locale rows |

Skipped: spec.md (no architecture doc delta beyond F36 row), dependency-inventory (no new dep per R63), README.

## Eval curation interview (Blocks A–F)

| Block | Outcome |
|-------|---------|
| A — Coverage | Community + housing + legal + edge; 10 cases; edge cases included |
| B — Questions | Q1–Q10 approved; housing/legal en-only v1 |
| C — Retrieval | URL-in-top-k; `any_of` for ambiguous row |
| D — Answer rubric | `required_facts[]` per row |
| E — Thresholds | Retrieval ≥80%; faithfulness/answer relevancy CI ≥0.60, display &lt;0.70; latency informational p95 30s; judge in query language |
| F — Privacy/roles | ADR-004 synthetic fixture only; admin-only access |

## Interview decisions

| ID | Decision |
|----|----------|
| RD-099 | Domains: community + housing + legal + edge |
| RD-100 | Size: 10 cases, 14 locale rows |
| RD-101 | Edge: abstain, ambiguous, empty retrieval |
| RD-102 | Golden questions Q1–Q10 approved |
| RD-103 | Housing/legal es deferred until #94 |
| RD-104 | Retrieval: URL in top-k |
| RD-105 | Answer rubric: `required_facts[]` |
| RD-106 | Retrieval threshold ≥80% |
| RD-107 | Faithfulness CI ≥0.60, display &lt;0.70 |
| RD-108 | Answer relevancy CI ≥0.60, display &lt;0.70 |
| RD-109 | Judge in query language |
| RD-110 | Admin-only eval access |
| RD-111 | Latency informational (p95 30s ref) |
| RD-112 | Tooling: LlamaIndex + custom (R63) |
| RD-113 | Feature ID F36 (R64) |

## Build handoff notes

- Existing `tests/eval/test_eval_retrieval_relevance.py` must be extended for `retrieval_expectation`
  and edge rows (TC-111, TC-113) — current 3-pair-only logic will not pass on expanded fixture alone.
- Postgres schema + eval runner placement → **04-tech-plan**
- Tooling ADR for R63 → **04-tech-plan**
- Coordinate groundedness metric with #84 when available

## Handoff

**Next stage:** 04-tech-plan (evolve-lite — 02/03/05/06 skipped per routing plan).

### Dashboard scope delta (2026-07-01, R68)

In-place **01-requirements delta** for interactive eval dashboard (M64). See
[01-requirements-dashboard-delta.md](./01-requirements-dashboard-delta.md).

| Artifact | Added |
|----------|-------|
| user-journeys | UJ-041–UJ-043 |
| test-plan | TC-117–TC-122 |
| acceptance-criteria | AC-E17–AC-E21 |
| api-contract | timeseries + criteria CRUD |
| decisions | RD-114–RD-122 |
