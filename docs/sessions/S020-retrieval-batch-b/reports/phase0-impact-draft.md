# EV-017 Phase 0 — impact draft (pending proceed gate)

> **Status:** draft for approval · **Session:** S020 · **Date:** 2026-08-02

## Approved intake (batch 1)

| Fn | Title | Shape |
|----|-------|-------|
| F43 | Answer / retrieval cache | Full H1 cascade: exact → semantic answer → retrieve-result → generate |
| F44 | Soft language filter (#162) | Config-gated L1 (default **off**) + empty-hit fixture |
| F45 | Cross-encoder rerank (#83/#161) | Spike + ship gate; no prod CE unless gate passes |

## Docs to update (Phase A)

| Doc | Delta |
|-----|-------|
| `feature-list.md` | F43–F45 Planned rows + details |
| `spec.md` | Cache cascade; L1 filter; CE optional path |
| `config-spec.md` | Cache keys/TTL/thresholds; `language_soft_fallback`; CE enable + model |
| `api-contract.md` | Cache hit observability if exposed; else none |
| `user-journeys.md` | UJ for cache hit; soft fallback; CE-reranked ask |
| `test-plan.md` / `acceptance-criteria.md` | TC/AC per Fn |
| `decisions.md` / evolve-decisions | RD + S020-D* |
| ADR | Prefer amend (cache policy / filter) over new unless CE deploy needs one |

## Code surfaces (Phase C — provisional)

| Area | F43 | F44 | F45 |
|------|-----|-----|-----|
| `packages/rag` | Cache helper + normalize | Soft L1 retrieve | CE client interface (spike/prod gate) |
| `apps/chat-rag-backend` | Wire cascade on ask | Flag-gated filter | Flag-gated CE after retrieve |
| F36 / eval harness | Cost + hit-rate cells | Empty-hit fixture | Spike scripts + gate metric |
| Modal | Unlikely (in-process first) | — | Spike CE on T4 (as S019) |

## Risks

| Risk | Mitigation |
|------|------------|
| Semantic cache false hits (faith↓) | Conservative threshold; log hits; quality ≥ H0 gate |
| CE fails again (R3 precedent) | Spike-only by default; ship gate mandatory |
| #162 unused on golden | Empty-hit fixture required; default off |
| ADR-004 identity leak | Content-hash keys only; no user/session keys |
| ADR-006 creep | No LangGraph this cycle (S019-D27) |

## Routing (unchanged)

Standard: `01 → 02 → 04 → 07 → 08 → 09 → 10 → 11 → 12 → 13` (skip 03/05/06/15).
