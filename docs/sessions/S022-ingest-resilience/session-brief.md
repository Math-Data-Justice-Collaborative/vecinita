---
session_id: S022-ingest-resilience
type: feature
status: in_progress
branch: evolve/EV-019-ingest-resilience
started_at: 2026-08-02
intent: "Ingest resilience — content_hash skip (#163), embed sub-batch/retry (#166), chunk overlap (#160); investigate→ship on shared write/embed path"
orchestrator: 16-evolve
evolve_cycle_id: EV-019
github_issues: [163, 166, 160]
predecessor: S021-retrieval-follow-on
predecessor_cycle: EV-018
context_briefs:
  - ./context-brief.md
standing_docs_touched:
  - docs/feature-list.md
  - docs/decisions/evolve-decisions.md
  - docs/spec.md
  - docs/config-spec.md
  - docs/user-journeys.md
  - docs/test-plan.md
  - docs/acceptance-criteria.md
  - docs/api-contract.md
  - docs/decisions.md
---

# Session S022 — Ingest resilience

## Intent

Ship ingest cost/latency and reliability improvements on the shared write/embed path:
skip no-op re-embeds when `content_hash` is unchanged, make embedding calls
sub-batch + retry resilient, and add chunk overlap (tokenizer-aligned sizing as needed).

Tickets are labeled investigate-first; this cycle **investigates then ships** in one evolve
(same posture as S019 Batch A).

## Predecessor

| Item | Ref |
|------|-----|
| Session | [S021-retrieval-follow-on](../S021-retrieval-follow-on/session-brief.md) |
| Cycle | EV-018 — completed; PR [#174](https://github.com/Math-Data-Justice-Collaborative/vecinita/pull/174) |
| Pipeline | Idle on `main` after RET-001 [#177](https://github.com/Math-Data-Justice-Collaborative/vecinita/pull/177) |

## Issues in scope

| Issue | Title | Role |
|-------|-------|------|
| [#163](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/163) | Skip re-ingest when `content_hash` unchanged | **F47** — primary cost/latency |
| [#166](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/166) | Embedding batch retries / sub-batching | **F48** — reliability |
| [#160](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/160) | Chunk overlap + tokenizer-aligned sizing | **F49** — included this cycle |

## Scope discipline

**In:**
- Trace hash → upsert → delete-chunks → re-embed; define skip + `force` semantics
- Sub-batch size + retry/backoff for `/embed/batch`; fail vs partial-success product choice
- Chunk overlap config + word≈token or tokenizer alignment; re-ingest notes if needed
- Spec/test/e2e deltas on admin ingest + write API + embed client
- Shared write/embed path only (no ChatRAG retrieval redesign)

**Out (unless Phase 0/01 expands):**
- Multilingual embed swap (#159)
- Context packing / top_k (#165 / #158) — Bundle B
- CE / #83 ship (F45) — flag stays off unless separate work
- Full corpus rebuild unless required by F49 ship decision
- Provider ABC / multi-embed backends

## Decisions (session open — 2026-08-02)

| ID | Decision |
|----|----------|
| S022-D1 | Open `feature` session **S022-ingest-resilience** (pipeline was idle) |
| S022-D2 | Scope = **A — Ingest resilience** (#163 + #166 + #160) |
| S022-D3 | Routing = **Standard**; skip 03, 05, 06, 15 unless later needed |
| S022-D4 | 00-context = **scoped** (no full regenerate / no org ecosystem scan) |
| S022-D5 | Posture = **investigate → ship** in one cycle (EV-019) |
| S022-D6 | Include **#160** in this cycle (not deferred) |
| S022-D7 | Continue with recommended after open → Phase 0 Fn lock → 01-requirements |
| S022-D8 | Fn ids: **F47** (#163), **F48** (#166), **F49** (#160) |
| S022-D9 | Ordering: F47 + F48 first (shared path), then F49 (chunking may force re-ingest) |
| S022-D10 | Deploy Path A default after verify |
| S022-D11 | Shared write/embed path only — no ChatRAG redesign |
| S022-D12 | Tagging stays ADR-023 fail-open; embeds get explicit retry (not silent fail-open) |
| S022-D13 | Phase 0 proceed — create EV-019 + start 01-requirements |
| S022-D14 | Phase 0C `1,1,1,2,2,1` — metadata refresh; fail URL; overlap 32; HF tokenizer; extend UJ |
| S022-D15 | F49 overlap default **32** |
| S022-D16 | F49 HF tokenizer (ADR-044) |
| S022-D17 | UJ-062 + TC-187–192 + AC-IR1–7 |
| S022-D18 | RD-219–RD-228 |
| S022-D19 | 01 complete → 02-verify-plan |

## Links

| Artifact | Path |
|----------|------|
| Routing plan | [routing-plan.md](./routing-plan.md) |
| HANDOFF | [HANDOFF.md](./HANDOFF.md) |
| 01 seed | [checkpoints/01-requirements-seed.md](./checkpoints/01-requirements-seed.md) |
| Context brief | [context-brief.md](./context-brief.md) |
