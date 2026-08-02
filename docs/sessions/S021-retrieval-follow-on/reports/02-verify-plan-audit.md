# 02-verify-plan audit — EV-018 / F46 + F45 re-gate

> **Session:** S021 · **Cycle:** EV-018 · **Date:** 2026-08-02  
> **Mode:** evolve delta · **Status:** completed (S021-D17 — M1–M4 approved)

## Inventory (delta)

| # | Document | Status |
|---|----------|--------|
| 1 | feature-list.md (F46; F45 EV-018 extension) | audited |
| 2 | spec.md (F46 retrieve reliability + F45 re-gate) | audited |
| 3 | user-journeys.md (UJ-061; UJ-060 prereq) | audited |
| 4 | test-plan.md (TC-185–186; TC-184 prereq) | audited |
| 5 | config-spec.md | audited — **no 01 delta** (intentional) |
| 6 | api-contract.md | audited — **no 01 delta** (intentional) |
| 7 | acceptance-criteria.md (AC-FO1–FO5; AC-BB9 prereq) | audited |
| 8 | decisions.md (RD-209–218) + evolve-decisions §EV-018 | audited |

## Consistency

| Check | Result |
|-------|--------|
| Feature ↔ Spec | Pass — F46 + F45 re-gate on ChatRAG / `packages/rag` |
| Feature ↔ Journey | Pass — UJ-061 (F46); UJ-060 (F45) |
| Journey ↔ Test | Pass — UJ-061 ↔ TC-185/186; UJ-060 ↔ TC-184 |
| Feature ↔ Test | Pass — F46 ↔ TC-185/186; F45 ↔ TC-184 |
| Spec ↔ Config | Pass deferred — no new knobs at 01; diagnose may unlock in 04 |
| Test ↔ Acceptance | Pass — AC-FO1↔TC-185; AC-FO2↔TC-186; AC-FO3–5 process; AC-BB9↔TC-184 |
| RD ↔ Spec / journeys | Pass — RD-209–218 mirror S021-D8–D16 |
| Scope boundaries | Pass — AC-FO5 / RD-218 out of scope holds |
| Connectivity | Pass — no browser UI change; API e2e only; no new CORS |
| Naming | Pass after M2 — F46 uses `min_retrieval_score` |
| Stale prose | Pass after M3 — F45 CE model locked to RD-213 |

## Verdicts

### Auto-approved (high confidence)

From S021-D8–D16 / RD-209–218 / locked L1–L14:

- F46 Planned — restore non-empty staging retrieve pools / ask `sources`
- F45 re-gate only after F46 / AC-FO1; same CE floors 0.28 / 0.91
- CE model remains `BAAI/bge-reranker-v2-m3` on Modal T4 (RD-213)
- Prod `VECINITA_RAG_RERANK_CE` stays **false** until AC-BB9 + deploy approval
- Ordering F46 → F45; two milestones, one cycle
- Outcome-based ACs; root cause classified in 04/07 (not locked in product specs)
- Defer BUG file until 07 code repro
- UJ-061 + TC-185/186 + AC-FO1–FO5; UJ-060/TC-184/AC-BB9 prereq F46
- Deploy Path A default; Path B only if corpus rebuild required
- Out of scope: LangGraph/ADR-006; #159 embeds; synthesizer upsizing; F43/F44 redesign
- No new API endpoints / OpenAPI at 01
- UI e2e none for this cycle

### Medium — approved (S021-D17)

| ID | Statement | Verdict |
|----|-----------|---------|
| M1 | TC-185 / AC-FO1 = representative non-empty pools (not every golden row > 0) | **Approved** |
| M2 | Align F46 knob name to `min_retrieval_score` in feature-list | **Approved** — surgical fix applied |
| M3 | Drop F45 “01 open Q” alternate-model text; keep `bge-reranker-v2-m3` | **Approved** — surgical fix applied |
| M4 | Root-cause class + optional BUG remain 04/07 — not Gate A→B blockers | **Approved** |

### Low / contradictions

None found after M2/M3 fixes.

## Source updates

| File | Change |
|------|--------|
| `docs/feature-list.md` | F46 Inputs/prose → `min_retrieval_score`; F45 CE model lock per RD-213 |

## Gate A→B

**Passed** (S021-D17). Phase A complete → Phase B `04-tech-plan` (03/05/06 skipped).
