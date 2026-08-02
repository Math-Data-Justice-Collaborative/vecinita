# 01-requirements seed — S020 / EV-017 (Retrieval Batch B)

Generated from 00-context session open (2026-08-02). Locked decisions are **confirm-only**.
Phase 0 intake may append more locked rows before 01 starts.

## How 01 should use this

1. Load this seed (not a greenfield interview).
2. Confirm locked decisions in one batch.
3. Apply document manifest deltas only.
4. Interview **only** open questions below (plus any Phase 0 adds).
5. Next after 01: `02-verify-plan`.

## Locked decisions

| Seed ID | Session ID | Decision |
|---------|------------|----------|
| L1 | S020-D1 | New session S020 (not reopen S019); predecessor EV-016/F42 LIVE |
| L2 | S020-D2 | One cycle EV-017 with **three tracks**: F43 cache + #83/#161 CE spike + #162 soft language |
| L3 | S020-D3 | Routing **Standard**; skip 03/05/06/15 |
| L4 | S019-D21 | Synthesizer remains `qwen2.5:1.5b-instruct` |
| L5 | S019-D27 | **No LangGraph / no ADR-006 amend** unless Phase 0 re-opens with evidence |
| L6 | S019 spike | F43 motivated by H1/H9: warm cache_hit≈1, quality≈H0; cost win not quality win |
| L7 | S019 R3 | Prior CE (`bge-reranker-base`) **failed** relevancy lift — do not ship from that evidence alone |
| L8 | S019 A3 | #162 soft fallbacks unused on staging golden — empty-hit / #54-class only |
| L9 | S020-D4 | F43 = full H1 cascade (exact → semantic answer → retrieve-result → generate) |
| L10 | S020-D5 | CE = spike + ship gate; no prod CE unless gate passes |
| L11 | S020-D6 | #162 = config-gated L1 default off + empty-hit fixture |
| L12 | S020-D7 | Pre-allocate F43 (cache), F44 (#162), F45 (CE) as Planned |

## Document manifest (delta — after Phase 0 lock)

| Document | Action |
|----------|--------|
| `docs/feature-list.md` | Add F43, F44, F45 (Planned) |
| `docs/spec.md` | Cache + optional filter/rerank deltas |
| `docs/config-spec.md` | Cache TTL/key/normalize; CE/filter flags if shipped |
| `docs/api-contract.md` | Only if cache observability or new endpoints |
| `docs/test-plan.md` / `acceptance-criteria.md` | TC/AC for F43 (+ others if ship) |
| `docs/user-journeys.md` | Cache hit journey; optional filter/rerank |
| `docs/decisions/evolve-decisions.md` | §Cycle EV-017 |
| `docs/adr/` | Only if new architecture (prefer amend existing over new unless needed) |

**Excluded:** regenerate full greenfield suite; re-open F42 packing; ADR-006 unless unlocked.

## Pre-filled interview answers (confirm/modify)

| Topic | Locked / proposed |
|-------|-------------------|
| F43 tiers | **Locked D4** — full H1 cascade |
| F43 surface | ChatRAG ask path + shared `packages/rag` helper; F36 harness can measure |
| Cache keys | Content-hash of normalized query (+ locale); no identity-keyed store (ADR-004) |
| Cache backend | In-process / ephemeral first; Modal volume only if 01 unlocks |
| Semantic threshold | Confirm in 01 (false-hit / faith risk) |
| CE ship bar | Staging golden relevancy ≥ F42 Hy1 floor **and** faith ≥ 0.91; else spike-only |
| #162 | **Locked D6** — config-gated L1 default off + empty-hit fixture |
| Fn ids | **Locked D7** — F43 / F44 / F45 |
| Success | F43: $/row or LLM-skip rate win with quality ≥ H0; F44/F45: gate or defer |

## Open questions for 01 (after Phase 0 proceed)

| ID | Question | Recommended default |
|----|----------|---------------------|
| Q1 | Semantic answer cosine threshold + false-hit policy? | Conservative threshold; miss → retrieve; log semantic hits |
| Q2 | CE model / host for renewed spike? | New candidate vs retry `bge-reranker-base`; Modal T4 playground |
| Q3 | Exact CE ship numbers (relevancy/faith floors)? | Relevancy ≥ Hy1 staging floor; faith ≥ 0.91 |
| Q4 | Deploy target | Staging Path A (write-api + chat-rag) like EV-016 |
| Q5 | Cache TTL / max entries / invalidation on corpus rebuild? | TTL + size cap; bust on F41 rebuild / corpus version |

## Explicitly out of interview scope

- Re-litigate F42 H7+P1 packing
- Model sweep / synthesizer upsizing
- #159 multilingual embeds
- LangGraph production path (unless user unlocks Q on ADR-006)

## Next after 01

`02-verify-plan` (delta consistency + statement audit on changed sections).
