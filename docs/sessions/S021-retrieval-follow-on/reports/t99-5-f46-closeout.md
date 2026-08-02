# T99.5 — F46 diagnose note + staging UJ-061 evidence

> **Session:** S021 · **Cycle:** EV-018 · **Date:** 2026-08-02  
> **Status:** completed · **Unblocks:** M100 (F45 CE re-gate)

## Root-cause class (final)

| Class | Detail |
|-------|--------|
| **Primary** | Staging live `embeddings` overwritten with test `basis_vector` one-hots (2026-08-02 02:45 UTC) via unguarded `attach_embeddings` UPSERT — BUG-2026-08-02 |
| **Secondary** | Prior E0 promote `e3a78965` covered only **2/49** docs — golden fixture URLs never fully re-embedded |
| **Not causal** | Language filters; missing golden URLs; permanent `min_retrieval_score` drop |

Diagnose trail: `diagnose-f46-empty-retrieve.md` → `promote-history-investigation.md` → Path B `t99-3-path-b-rebuild.md`.

## Staging UJ-061 / AC-FO1 evidence path

| Artifact | Path |
|----------|------|
| Pre-fix probe | `reports/probe-retrieve-pools.json` (rewritten post–Path B) |
| Path B rebuild JSON | `reports/path-b-e0-rebuild.json` |
| Path B narrative | `reports/t99-3-path-b-rebuild.md` |
| Ops script | `scripts/path_b_e0_full_reembed.py` |
| Promote run | `a0e8f32d-7e2e-4012-960c-2e956ceeba87` — **49 docs / 213 chunks** |

| Check | Before | After Path B |
|-------|--------|--------------|
| empty@0.2 | 8/8 | **0/8** |
| top scores | ~0.03–0.07 | **~0.68–0.83** |
| one-hot vectors | ~213 | **0** |
| rifreeclinic live↔Modal cosine | ≈ −0.05 | **1.0** |

**Verdict:** AC-FO1 met on staging (representative non-empty pools). AC-FO2 covered by TC-186 (cold ask `sources`). UJ-061 unblocks UJ-060 / M100.

## E2E closeout pointer

`t99-4-e2e-closeout.md` — S021-D23 local Docker waiver; TC-185 CI-gated.
