# EV-016 S019-D36 — E1 F41 shadow + Hy1 F36

> **Artifact:** `eval-experiments/20260801T130441Z_e1-shadow-f36.json`  
> **Shadow:** `rebuild_run_id=1fa1dec9-f5a0-4670-afa2-a71fe039d479`  
> **Model:** `intfloat/multilingual-e5-small` (E1) · synthesizer `qwen2.5:1.5b-instruct`  
> **Not promoted** — live corpus still E0

## Setup

1. F41 dry_run rebuild stamped E1; 211 shadow chunks via Modal sentence-transformers encode  
2. Query embed on shadow path uses E1 (`query:` prefix); E0 cells use prod FastEmbed  
3. Cells: E0_Hy0, E0_Hy1, E1_Hy0, E1_Hy1 on expanded staging golden (18 rows; 7 ES)

## Hy1 compare (ship-relevant)

| Metric | E0_Hy1 | E1_Hy1 | Δ |
|--------|--------|--------|---|
| answer_relevancy | **0.278** | 0.111 | **−0.167** |
| en relevancy | **0.364** | 0.091 | **−0.273** |
| es relevancy | 0.143 | 0.143 | 0 |
| retrieval | 0.875 | **0.938** | +0.063 |
| es retrieval | 0.714 | **1.00** | +0.286 |
| faith | 0.875 | **0.938** | +0.063 |
| lang_match | 1.00 | 1.00 | 0 |

## Verdict

**Do not ship E1 in F42.** Same-run F36 shows EN answer-relevancy regression and no ES
relevancy lift. E1 helps dense ES hit rate / faith slightly, but fails the lift bar for
answer quality.

Keep **F42 = H7+P1 on E0**. Leave #159 open for a later FastEmbed-capable multilingual
candidate or judge-stable re-measure — not this cycle’s ship.

## Notes

- Judge noise remains high across runs (E0_Hy0 relevancy swung vs prior attempt); **within-run**
  E0_Hy1 vs E1_Hy1 is the decision signal.
- One faithfulness judge 502 occurred mid E0_Hy1 (logged); retries elsewhere succeeded.
