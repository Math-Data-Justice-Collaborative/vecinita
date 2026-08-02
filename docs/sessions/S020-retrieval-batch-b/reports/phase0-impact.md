# EV-017 Phase 0 — impact analysis (approved)

> **Status:** `phase0_approved` (S020-D8) · **Session:** S020 · **Date:** 2026-08-02  
> **Supersedes:** `phase0-impact-draft.md`

## Feature allocation

| Fn | Title | Status | Issues |
|----|-------|--------|--------|
| **F43** | Answer / retrieval cache (H1 cascade) | Planned | — (cost track) |
| **F44** | Soft language filter / empty-hit fallback | Planned | #162 |
| **F45** | Cross-encoder rerank spike + gated ship | Planned | #83 / #161 |

## Intake lock

| ID | Decision |
|----|----------|
| S020-D4 | F43 = full H1 cascade |
| S020-D5 | F45 = spike + ship gate |
| S020-D6 | F44 = config-gated L1 default off + empty-hit fixture |
| S020-D7 | Pre-allocate F43–F45 |
| S020-D8 | Proceed → Fn rows + impact + start 01-requirements |

## Docs to update (Phase A — 01)

| Doc | Delta |
|-----|-------|
| `feature-list.md` | **Done** — F43–F45 + F42 → Implemented |
| `spec.md` | Cache cascade; L1 filter; CE optional path |
| `config-spec.md` | Cache TTL/keys/thresholds; soft language flag; CE flags |
| `api-contract.md` | `cache_hit` observability if response metadata expands |
| `user-journeys.md` | UJ-057+ for cache / soft fallback / CE-gated ask |
| `test-plan.md` / `acceptance-criteria.md` | TC/AC per Fn |
| `decisions.md` | RD range for EV-017 |
| ADR | Only if CE ship or cache backend needs one |

## Code surfaces (Phase C — provisional)

| Area | F43 | F44 | F45 |
|------|-----|-----|-----|
| `packages/rag` | Cascade helpers | L1 retrieve | CE client (if ship) |
| `apps/chat-rag-backend` | Wire ask/stream | Flag-gated | Flag-gated post-gate |
| F36 / harness | Cost + hit-rate | Empty-hit fixture | Spike + gate |
| Modal | Unlikely first | — | CE spike T4 |

## Risks & mitigations

| Risk | Mitigation |
|------|------------|
| Semantic false hits | Conservative threshold; quality ≥ H0 |
| CE fails again | Spike-only default; mandatory ship gate |
| #162 unused on golden | Empty-hit fixture; default off |
| ADR-004 | Content-hash keys only |
| ADR-006 | No LangGraph |

## Routing

Standard: `01 → 02 → 04 → 07 → 08 → 09 → 10 → 11 → 12 → 13` (skip 03/05/06/15).

## Next

**01-requirements** (delta) — load seed; confirm locked; resolve open Qs; write remaining specs.
