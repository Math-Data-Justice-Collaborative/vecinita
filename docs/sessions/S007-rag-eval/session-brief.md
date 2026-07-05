---
session_id: S007-rag-eval
type: feature
status: in_progress
branch: feat/S007-rag-eval
started_at: 2026-07-01
intent: "GitHub #99 — admin RAG evaluation tab, expanded bilingual golden set, eval runner with metrics + history. Tooling: LlamaIndex evaluators + custom harness (R63). Golden prompts/results via 01-requirements interview (R67)."
orchestrator: 16-evolve
evolve_cycle_id: EV-008
context_briefs:
  - docs/sessions/S000-internal-docs-archive/context/rag-eval.md
standing_docs_touched:
  - docs/feature-list.md
  - docs/user-journeys.md
  - docs/test-plan.md
  - docs/acceptance-criteria.md
  - docs/api-contract.md
  - docs/config-spec.md
  - docs/deployment-integration.md
  - docs/eval-golden-set.md
  - docs/decisions.md
  - data/fixtures/eval/qa_pairs.json
linked_issues:
  - 99
parent_session: null
paused_sessions:
  - S006-invite-acceptance
---

# Session S007 — RAG evaluation tab + golden set

## Intent

Deliver **F36**: admin-only evaluation of the RAG pipeline against a maintained golden set
(retrieval relevance, faithfulness/groundedness, answer relevance, latency) with run history
in the data-management UI. Unblock #99's tooling decision with **LlamaIndex native evaluators**
plus custom persistence and admin tab — no Langfuse/Ragas/DeepEval for v1.

Tracked in [GitHub #99](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/99).

## Scope

**In scope**

- Tooling ADR (R63) + dependency-inventory note (no new eval package)
- **Golden eval content via user interview (R67)** — questions, expected sources, reference answers/key facts, thresholds, judge guidelines → see [eval-curation-plan.md](./reports/eval-curation-plan.md)
- Golden set expansion (`data/fixtures/eval/`) — **after** 01-interview sign-off
- Eval runner through `packages/rag` + Modal LLM judge
- Postgres persistence + `internal-write-api` endpoints
- Admin `/evaluation` tab (en/es i18n)
- Harness tests + admin UI e2e

**Out of scope (v1)**

- Langfuse / Phoenix / Ragas / DeepEval integration
- Public eval UI
- Auto prompt/model tuning
- Production trace observability platform

## Routing plan

See [routing-plan.md](./routing-plan.md).

## Decisions (session open)

| ID | Decision |
|----|----------|
| R63 | LlamaIndex native evaluators + custom harness/Postgres/admin UI |
| R64 | Feature ID **F36** (not F34 — already Supabase auth) |
| R65 | Park S006; open S007 |
| R66 | evolve-lite routing (skip 02,03,05,06,11) |
| R67 | Golden prompts + expected results + judge guidelines via **01-requirements interview** |

## Links

- Context: [rag-eval.md](../../sessions/S000-internal-docs-archive/context/rag-eval.md)
- Eval interview plan: [eval-curation-plan.md](./reports/eval-curation-plan.md)
- Paused: [S006-invite-acceptance](../S006-invite-acceptance/session-brief.md) (#109)
- Related issues: #83 (reranking), #84 (groundedness), #94 (corpus)
