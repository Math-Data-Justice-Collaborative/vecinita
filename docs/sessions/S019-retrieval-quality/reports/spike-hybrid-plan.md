# EV-016 hybrid iterate plan (Phase 0)

> **Session:** S019 · **Cycle:** EV-016 · **Status:** option **A** done — ship lean pending `phase0_approved`  
> **Date:** 2026-08-01  
> **Inputs:** A0–A4(+R3), model sweep (closed), harness H0–H9  
> **Metrics:** S019-D30 — EN/ES breakdown, answer_lang_match, cross_lang_share  
> **Artifact:** `eval-experiments/20260801T002819Z_hybrid-sweep.json`

## Scoreboard (staging golden, control 1.5B)

| Cell | relevancy | faith | Role |
|------|-----------|-------|------|
| R0+P1 packing | 0.23 | 0.91 | Safe floor (F42 core) |
| **R1+P1** | **0.31** | 0.82 | Cheap heuristic rerank — faith tradeoff |
| **H7 fan-out** | **0.31** | 0.91 | Only harness quality win — faith held |
| H1 / H9 answer cache | 0.23 | 0.91–1.0 | Cost win (llm/row→0 warm) |
| R3 CE / H2 prefix / #162 / model upsizing | ≤0.23 or ↓ | — | **Reject** |

## Hybrid thesis

Packing alone tops out at **0.23**. Two independent levers each reach **0.31**:
**R1+P1** (faith −0.09) and **H7** (faith held). They were **not** combined on one
run. Next Phase 0 step = measure the stack before freezing ship scope.

```
retrieve (top_k≥8 pool)
  → optional H7: 2–3 query rewrites → merge / dedupe docs
  → optional R1: title-overlap × dense + doc diversity → keep_k
  → P1/P3 pack (headers + dedupe + budget)
  → synth 1.5B
  → optional H1 answer cache (cost lane, not quality)
```

## Proposed ship layers

| Layer | Content | Fn | Gate |
|-------|---------|-----|------|
| **L0 prereq** | ISS-008 Admin staging golden fixture | hotfix-in-cycle | Before promote smoke |
| **L1 quality core** | Shared P1/P3 packer (#165) | **F42** | Always ship |
| **L2 quality boost** | Thin multi-query fan-out (H7) — **no LangGraph / no ADR-006** | F42 expand **or** F43 | Ship only if hybrid cell ≥ H7 alone and faith ≥ 0.91 |
| **L2b optional** | R1 heuristic rerank (#161 cheap) | same Fn or config flag | Ship only if hybrid faith ≥ 0.85 **or** user accepts 0.82 |
| **L3 cost** | Answer / retrieve cache (H1/H9) | **F43** | Separate; no LangGraph |
| **Out** | CE (R3), H2, #162, model change, full #83, LangGraph | — | Deferred |

## Hybrid eval cells (S019-D29 = A)

Runner: `scripts/spike_hybrid_sweep.py`. Staging golden + 1.5B.

| ID | Stack | Expect / role |
|----|-------|----------------|
| Hy0 | R0+P1 | = 0.23 / 0.91 (control) |
| Hy1 | H7+P1 | ≥ 0.31 / ≥ 0.91 |
| Hy2 | H7+P3 | hygiene vs Hy1 |
| Hy3 | H7+R1+P1 | relevancy ?; faith watch |
| Hy4 | H7+R1+P3 | production-shaped |
| HyLang0 | L0+R0+P1 | prod language filter + packing (A3 rerun) |
| HyK8 | R0+P1+k=8 | A1 top_k rerun with packing |

### Extra metrics (S019-D30)

Per cell and **by_locale (en / es)**:

- `retrieval_relevance`, `faithfulness`, `answer_relevancy`, `latency_p95_ms`
- `answer_lang_match_rate` — detected answer lang == golden locale
- `mean_cross_lang_share` — fraction of packed chunks ≠ query lang
- `mean_context_chars`, per-row `chunk_languages` / `n_docs`

H7 rewrites are Spanish-aware for `locale=es`.

**Stop rules**

1. If **Hy1** ≤ Hy0 → drop H7 from ship; F42 = packing only.  
2. If **Hy3** faith &lt; 0.85 and relevancy lift ≤ Hy1 → drop R1; keep H7+P*.  
3. If no hybrid beats Hy0 on relevancy with faith ≥ 0.91 → ship **F42 packing only**.  
4. Cache (L3) does not need hybrid cells — already proven H1/H9.
5. If **es** relevancy or `answer_lang_match` collapses under a cell → do not ship that cell without a lang fix.

## Iteration options

| Option | Status |
|--------|--------|
| **A — Measure then ship** | **Locked** (S019-D29) |
| B / C / D | Not selected |

## Out of this iterate

- ADR-006 amend (D27 still holds — H7 is a thin helper, not a graph ship)
- Playground GPU changes (stay T4 / D26)
- Reopening model sweep

## Hybrid sweep results (20260801T002819Z)

| Cell | stack | retrieval | faith | relevancy | lang_match | cross_lang | en_rel | es_rel | p95_ms |
|------|-------|-----------|-------|-----------|------------|------------|--------|--------|--------|
| Hy0 | R0+P1 | 1.00 | 0.91 | 0.23 | 1.00 | 0.15 | 0.27 | **0.00** | 5804 |
| **Hy1** | **H7+P1** | 1.00 | **0.91** | **0.31** | 1.00 | 0.15 | **0.36** | **0.00** | 5010 |
| Hy2 | H7+P3 | 1.00 | 0.91 | 0.19 | 1.00 | 0.15 | 0.23 | 0.00 | 5446 |
| Hy3 | H7+R1+P1 | 1.00 | **0.82** ↓ | 0.31 | 1.00 | 0.15 | 0.36 | 0.00 | 4731 |
| Hy4 | H7+R1+P3 | 1.00 | 0.82 ↓ | 0.19 | 1.00 | 0.15 | 0.23 | 0.00 | 5378 |
| HyLang0 | R0+P1+L0 | 0.91 ↓ | 0.91 | 0.23 | 1.00 | **0.00** | 0.27 | 0.00 | 5054 |
| HyK8 | R0+P1+k8 | 1.00 | 0.91 | 0.23 | 1.00 | 0.15 | 0.27 | 0.00 | 5182 |

Artifact: `eval-experiments/20260801T002819Z_hybrid-sweep.json`

### Stop-rule application

1. **Hy1 > Hy0** (0.31 vs 0.23), faith held → **keep H7**.  
2. **Hy3** faith 0.82 &lt; 0.85, relevancy = Hy1 → **drop R1**.  
3. Quality win with faith ≥ 0.91 → ship **H7+P1**, not packing-only.  
4. **P3 (Hy2/Hy4) hurts relevancy** vs P1 → pack headers first; dedupe/budget optional hygiene later.  
5. **HyK8** no lift over Hy0 → top_k=8 secondary only.  
6. **HyLang0** = Hy0 relevancy; retrieval 0.91; cross_lang→0 (prod L0 hygiene).  
7. **Spanish:** `answer_lang_match=1.0` and faith=1.0 on both `es` rows, but **es_rel always 0.0** (n=2). H7 raises es `cross_lang` (0.4→0.6). Track as follow-on (judge / more es golden / same-lang merge); do not block EN quality ship.

### Ship lean (pending phase0_approved)

**F42 = P1 packing + thin H7 multi-query fan-out** (no LangGraph, no R1, no CE).  
**Out this cycle:** R1, P3-as-default, #162 soft filter, F43 cache (later), ADR-006 amend.  
**Prereq:** ISS-008 before Admin promote smoke.

## Next

1. AskQuestion `phase0_approved` on F42 = H7+P1  
2. Enter Phase A `01-requirements`  
3. Fix ISS-008 on ship path  
4. Optional follow-on: Spanish relevancy / es golden expansion (not F42 blocker)

## Hybrid sweep results (20260802T020137Z)

| Cell | stack | retrieval | faith | relevancy | lang_match | cross_lang | en_rel | es_rel | p95_ms |
|------|-------|-----------|-------|-----------|------------|------------|--------|--------|--------|
| Hy1 | H7+P1 | 0.875 | 0.9375 | 0.16666666666666666 | 1.0 | 0.18888888888888888 | 0.2727272727272727 | 0.0 | 7559 |

Artifact: `eval-experiments/20260802T020137Z_hybrid-sweep.json`

## Hybrid sweep results (20260802T022041Z)

| Cell | stack | retrieval | faith | relevancy | lang_match | cross_lang | en_rel | es_rel | p95_ms |
|------|-------|-----------|-------|-----------|------------|------------|--------|--------|--------|
| Hy1 | H7+P1 | 0.875 | 0.9375 | 0.16666666666666666 | 1.0 | 0.18888888888888888 | 0.2727272727272727 | 0.0 | 7401 |

Artifact: `eval-experiments/20260802T022041Z_hybrid-sweep.json`

## Hybrid sweep results (20260802T022407Z)

| Cell | stack | retrieval | faith | relevancy | lang_match | cross_lang | en_rel | es_rel | p95_ms |
|------|-------|-----------|-------|-----------|------------|------------|--------|--------|--------|
| Hy1 | H7+P1 | 0.9375 | 0.9375 | 0.16666666666666666 | 1.0 | 0.13333333333333336 | 0.2727272727272727 | 0.0 | 8793 |

Artifact: `eval-experiments/20260802T022407Z_hybrid-sweep.json`

## Hybrid sweep results (20260802T022836Z)

| Cell | stack | retrieval | faith | relevancy | lang_match | cross_lang | en_rel | es_rel | p95_ms |
|------|-------|-----------|-------|-----------|------------|------------|--------|--------|--------|
| Hy1 | H7+P1 | 0.9375 | 0.9375 | 0.8333333333333334 | 1.0 | 0.13333333333333336 | 0.8181818181818182 | 0.8571428571428571 | 7469 |

Artifact: `eval-experiments/20260802T022836Z_hybrid-sweep.json`
