# 01-requirements seed — S021 / EV-018 (Retrieval follow-on)

Generated from 00-context session open (2026-08-02). Locked decisions are **confirm-only**.
Phase 0 intake (16-evolve) may append more locked rows before 01 starts.

## How 01 should use this

1. Load this seed (not a greenfield interview).
2. Confirm locked decisions in one batch.
3. Apply document manifest deltas only.
4. Interview **only** open questions below (plus any Phase 0 adds).
5. Next after 01: `02-verify-plan`.

## Locked decisions

| Seed ID | Session ID | Decision |
|---------|------------|----------|
| L1 | S021-D1 | New session S021 (not reopen S020); predecessor EV-017 @ `f24a620` |
| L2 | S021-D2 | One cycle: **empty retrieve fix + CE re-gate** |
| L3 | S021-D3 | Routing **Standard**; skip 03/05/06/15 |
| L4 | S021-D4 | 00 scoped delta — reuse S020 CE/retrieve evidence |
| L5 | S020-D12 / S021-D6 | CE floors: relevancy ≥ **0.28**, faith ≥ **0.91** |
| L6 | S020-D21 / S021-D7 | Prod `VECINITA_RAG_RERANK_CE` stays **false** until re-gate + deploy approval |
| L7 | S019-D27 | **No LangGraph / no ADR-006 amend** unless Phase 0 re-opens |
| L8 | S019-D21 | Synthesizer remains `qwen2.5:1.5b-instruct` |
| L9 | S020 Path A | F43/F44 shipped; F45 remains spike-only until this cycle proves otherwise |
| L10 | S020 CE | Spike model **`BAAI/bge-reranker-v2-m3`** on Modal T4 (unless Phase 0 changes) |
| L11 | S021-D8 | Fn ids: **F46** (retrieve reliability) + extend **F45** (CE re-gate) |
| L12 | S021-D9 | Ordering: **F46 first**, then F45 re-gate (same cycle) |
| L13 | S021-D10 | Planned Fn in evolve (not nested hotfix by default) |
| L14 | S021-D11 | Deploy **Path A** default; Path B only if corpus rebuild required |

## Document manifest (delta — after Phase 0 Fn lock)

| Document | Action |
|----------|--------|
| `docs/feature-list.md` | **Done Phase 0** — F46 + F45 EV-018 note; refine status after re-gate in 01/13 |
| `docs/spec.md` | Retrieve reliability / staging corpus pin notes if behavior changes |
| `docs/config-spec.md` | Only if `min_score` / retrieve knobs change |
| `docs/test-plan.md` / `acceptance-criteria.md` | AC/TC for non-empty retrieve + CE re-gate |
| `docs/user-journeys.md` | UJ-060 update; optional retrieve-health journey |
| `docs/decisions/evolve-decisions.md` | §Cycle EV-018 |
| `docs/bug-reports/` / `tests/bugs/` | If classified as bug with repro (14-hotfix pattern inside evolve) |

**Excluded:** regenerate full greenfield suite; reopen F42/F43/F44 design; ADR-006 unless unlocked.

## Pre-filled interview answers (confirm/modify)

| Topic | Locked / proposed |
|-------|-------------------|
| Root symptom | Empty retrieve pools on staging golden + live H3 (faith null) |
| CE ship bar | Unchanged floors unless Phase 0 AskQuestion changes |
| CE model | Keep `bge-reranker-v2-m3` / T4 unless new hypothesis |
| Success | Non-empty pools on golden; then AC-BB9 pass **or** documented re-spike-only |
| Fn ids | **Locked D8** — F46 + extend F45 |
| Deploy | **Locked D11** — Path A default; Path B if corpus rebuild |
| Ordering | **Locked D9** — F46 then F45 re-gate |

## Open questions — resolved (01 Phase 0C — 2026-08-02)

| ID | Resolution |
|----|------------|
| Q1 | Outcome-based ACs; root cause in 04/07 (S021-D13) |
| Q2 | UJ-061 + TC-185/186 + AC-FO1–FO5; amend UJ-060 (S021-D15) |
| Q3 | Defer BUG file until 07 code repro (S021-D14) |
| Q4 | Same cycle, two milestones — F46 then F45 (S021-D9) |
| Locked L1–L14 | Approved all (S021-D16) |

## Remaining for 04 / 07

| ID | Question |
|----|----------|
| R1 | Root cause class after diagnose: pin vs min_score vs fixtures vs code? |
| R2 | If code bug: BUG slug + e2e layer at symptom surface |

## Explicitly out of interview scope

- Re-litigate F43 H1 cascade / F44 soft language defaults
- Model sweep / synthesizer upsizing
- #159 multilingual embeds
- LangGraph production path (unless user unlocks)

## Next after 01

`02-verify-plan` (delta consistency + statement audit on changed sections).
