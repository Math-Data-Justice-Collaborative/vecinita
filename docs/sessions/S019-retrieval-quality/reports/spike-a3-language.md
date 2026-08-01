# EV-016 spike A3 — soft language filter (#162)

> **Session:** S019 · **Cycle:** EV-016 · **Decision:** S019-D13  
> **Date:** 2026-07-31  
> **Artifact:** `spike-a3-language.json` · script `scripts/spike_a3_language.py`

## Setup

- Staging golden (`qa_pairs_staging.json`), top_k=5, min_score=0.2, packing **P0** (isolate language)
- **L_none** — no language filter (matches prior A0/A2/A4 retrieve path)
- **L0** — strict `d.language = detect_query_language` (prod ChatRAG)
- **L1** — same-lang first; if empty → retry without language
- **L2** — same-lang first; if empty → opposite language only

## Results (single run)

| Cell | retrieval | faith | relevancy | first_empty | fallback | empty_final | mean cross-lang share |
|------|-----------|-------|-----------|-------------|----------|-------------|------------------------|
| L_none | **1.00** | 0.91 | 0.15 | 0 | 0 | 0 | 0.15 |
| **L0** | **0.91** ↓ | 0.91 | **0.19** | 0 | 0 | 0 | 0.00 |
| L1 | 0.91 | 0.91 | 0.19 | 0 | **0** | 0 | 0.00 |
| L2 | 0.91 | 0.91 | 0.19 | 0 | **0** | 0 | 0.00 |

## Interpretation

1. **Soft fallbacks never fire** on this golden — every row has same-lang chunks above min_score under L0. L1 ≡ L2 ≡ L0.
2. **L0 vs prior spikes:** A0–A4 retrieved with **no** language filter (`L_none`). Prod is stricter; that costs one retrieval hit (`community-vecinita-intro` / en — expected URL only appears when cross-lang chunks are allowed). Soft empty-fallback does **not** recover it, because first pass is non-empty.
3. **Relevancy:** L0/L1/L2 slightly higher than L_none (0.19 vs 0.15) with faith flat — language-matched context may help a little, but absolute scores remain low and single-run noisy.
4. **#162 empty-hit hypothesis is not stressed** by staging golden. Soft filter cannot show F36 lift here. Keep #162 open for #54-class monolingual miss cases; do not ship from this golden alone.

## Miss detail (L0)

| Row | Why |
|-----|-----|
| `community-vecinita-intro` / en | Expected URL missing among top-5 **en** chunks; present under L_none (cross-lang mix). Not an empty-first-pass case → L1/L2 no-ops. |
| `edge-empty-quantum` / en | Unscored / empty expectation path (also fails under L_none). |

## Spike scoreboard (best cells so far)

| Approach | relevancy | faith | notes |
|----------|-----------|-------|-------|
| A0 dense k=5 (L_none) | ~0.08–0.15 | 0.91 | prior spikes |
| A1 k=8 | 0.19 | 0.91 | retrieval saturated |
| A2 P1 packing | 0.23 | 0.91 | best safe packing |
| A4 R1+P1 | **0.31** | 0.82 | best relevancy; faith tradeoff |
| A4 R0+P1 | 0.23 | 0.91 | safest packing-only |
| A3 L0/L1/L2 | 0.19 | 0.91 | **no soft-filter lift**; fallbacks unused |

## Recommendation

**Do not allocate F42 to #162 from this run.** Soft language filter is a coverage/empty-hit tool, not a relevancy lever on the current staging golden.

## Next (AskQuestion)

Lock ship candidate (P1 ± R1), try R3 CE, or stop spike / other.
