# EV-016 model prompt baseline (S019-D32)

> **Run:** `20260801T011751Z` · **Judge:** `qwen2.5:1.5b-instruct` (prod)  
> **Bare** = empty system prompt · **prompt_*** = `DEFAULT_EVAL_SYSTEM_PROMPT`  
> **Models:** control + Tiny (T4) · Artifact: `eval-experiments/20260801T011751Z_model-prompt-baseline.json`

## Why this run

Prior model sweep always used the eval system prompt + P1, and every model tied at
relevancy **0.23**. This run establishes a **no-prompt floor** per model and measures
which “improvements” actually move the needle.

| Condition | System prompt | Pack | H7 |
|-----------|---------------|------|----|
| `bare_p0` | **none** | P0 concat | no |
| `bare_p1` | **none** | P1 headers | no |
| `prompt_p1` | DEFAULT eval | P1 | no |
| `prompt_h7p1` | DEFAULT eval | P1 | yes |

## Results (all four models identical)

| Condition | retrieval | faith | relevancy | en_rel | es_rel | lang_match |
|-----------|-----------|-------|-----------|--------|--------|------------|
| **bare_p0** | 1.00 | **1.00** | 0.19 | 0.23 | 0.00 | 1.00 |
| bare_p1 | 1.00 | 0.91 | 0.19 | 0.23 | 0.00 | 1.00 |
| prompt_p1 | 1.00 | 0.91 | 0.23 | 0.27 | 0.00 | 1.00 |
| **prompt_h7p1** | 1.00 | 0.91 | **0.31** | **0.36** | 0.00 | 1.00 |

Models measured: `qwen2.5:1.5b-instruct` (prod), `g9v3:3b`, `qwen3:4b-instruct-2507`,
`minicpm5:1b` (playground). Metrics matched to float precision across all four.

## Deltas (same for every model)

| Lift | Δ relevancy | Δ faith | Meaning |
|------|-------------|---------|---------|
| Pack (`bare_p1` − `bare_p0`) | **0.00** | **−0.09** | Headers alone do not help relevancy; slight faith cost |
| Prompt (`prompt_p1` − `bare_p1`) | **+0.04** | 0.00 | Eval system prompt helps a little |
| Hybrid (`prompt_h7p1` − `prompt_p1`) | **+0.08** | 0.00 | **Largest lever** (H7 fan-out) |
| Total vs bare_p0 | **+0.12** | **−0.09** | Stack wins on relevancy; bare has best faith |

## Interpretation

1. **Bare floor exists:** without any system prompt, relevancy ≈ **0.19** and faith is
   **1.00** — better faith than the prompted cells.
2. **Improvements are stack effects, not model effects:** prompt + H7 reproduce the Hy1
   lift (→ 0.31) on every Tiny/control model the same way.
3. **Still no synthesizer winner** among control + Tiny under bare or improved conditions
   (same pattern as S019-D21). Control on **prod** matched playground Tiny → not a
   playground “stuck model” artifact for the control comparison.
4. **Spanish relevancy remains 0.00** (n=2) with `lang_match=1.0` in every cell.
5. **Caveat:** answers were not persisted in the JSON (metrics only). A follow-up can dump
   answer digests to prove models differ in text even when judges tie.

## Ship implication (still pre-`phase0_approved`)

- Quality gains come from **H7 + prompt (+ P1 in the prompted path)**, not from swapping
  Tiny synthesizers.
- Bare faith=1.0 suggests prompt wording may trade faith for relevancy — worth a prompt
  ablation later, separate from F42 packing/H7.
- S* / larger models not re-run here (playground on T4). Re-open only if user wants
  GPU upsizing again.

## Next options

1. Approve F42 = H7+P1 with this evidence  
2. Persist answer digests + re-run one model pair to prove text diversity  
3. Extend matrix to S* AWQ/A100 models  
4. Prompt wording ablation (keep H7+P1 fixed)  
