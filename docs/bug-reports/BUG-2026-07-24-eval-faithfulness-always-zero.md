# BUG-2026-07-24 — Eval faithfulness always 0 / relevancy under-parsed

**Status:** fixed  
**Severity:** high  
**Feature:** F36 / EV-008 RAG evaluation  
**Reported:** 2026-07-24

## Error description

Golden sweeps with judges enabled (`hf-picks-judges-*`) reported
**faithfulness=0.0** on every config and most rows, including Free Clinic answers
that were clearly supported by retrieved context. Custom rubrics
(`grounded-in-context`, `no-invented-pii`) were also 0.0. Answer relevancy was
sparse/low because the Qwen judge often emits `[FINAL RESULT]` instead of
`[RESULT]`, which the parser did not accept.

## Error logs

Live probe (staging retrieval + prod `qwen2.5:1.5b-instruct` judge):

```text
n_chunks 5 context_len 7826 truncated 5000
faith score 0.0 passing False
faith feedback 'NO'   # LlamaIndex FaithfulnessEvaluator / SummaryIndex path

# Same facts, direct YES/NO prompt:
direct wrapped: 'YES'
raw YES/NO: 'YES'

# Relevancy feedback (parse returned None):
[FINAL RESULT]
3
parse alone (None, '...')
```

Sweep aggregate (`hf-picks-judges-topk5-bothprompts`): all 12 groups
`faithfulness: 0.0`.

## Investigation

| Time (UTC) | Note |
|---|---|
| 2026-07-24 | Skip-judge sweep: retrieval 100% after re-embed |
| 2026-07-24 | Judges sweep: faith=0 everywhere; grounded invents mayor phone |
| 2026-07-24 | Short synthetic context → FaithfulnessEvaluator YES/1.0 |
| 2026-07-24 | Real top-1 Free Clinic chunk → FaithfulnessEvaluator NO; direct YES/NO → YES |
| 2026-07-24 | Root cause: SummaryIndex eval path unreliable with Modal/Qwen; relevancy parser misses `[FINAL RESULT]` |

## Root cause

1. **Faithfulness:** `FaithfulnessEvaluator` builds a `SummaryIndex` query engine and
   asks the LLM via refine templates. With Modal HTTP + Qwen instruct wrapping,
   real corpus chunks consistently produce `NO` even when every claim is in context.
   A direct “reply YES or NO” prompt on the same inputs returns `YES`.

2. **Answer relevancy:** `parse_answer_relevancy_output` only recognized `[RESULT]`,
   `[SCORE]`, and `Final Result:` — not Qwen’s `[FINAL RESULT]\nN`, so
   `EvaluationResult.score` stayed `None` → normalized to 0.0.

## Repro test

- `tests/bugs/test_bug_2026_07_24_eval_faithfulness_always_zero.py`
- `tests/unit/eval/test_eval_parsers.py` (FINAL RESULT + faithfulness YES/NO)

## Fix

- Direct binary faithfulness scoring via `llm.complete` + `parse_faithfulness_output`
- Extend relevancy parser for `[FINAL RESULT]`
- Tighten system prompts for abstain / no invented contact details

## TDD iteration log

| Step | Result |
|---|---|
| Red | Parser + direct faith unit tests fail before fix |
| Green | After judges.py / eval_parsers.py changes |
| Validate | Live probe: supported answer faith=1.0 / invented=0.0; relevancy=1.0 |
| Validate | Sweep `postfix-3b-prompts-judges`: faith 0.93–1.0 (was 0.0) |
| Residual | `grounded` still invents mayor phone from OB-GYN chunk; prefer `concise` |
