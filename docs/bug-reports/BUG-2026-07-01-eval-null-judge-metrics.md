# BUG-2026-07-01 — Eval UI metrics null (faithfulness / answer relevancy)

**Status:** fixed (pending deploy)  
**Severity:** high  
**Feature:** F36 / EV-008 RAG evaluation  
**Reported:** 2026-07-01

## Error description

Admin evaluation run `9c9980f8-0af0-43de-ad04-6c45a7409581` completed but
`metrics_summary` and per-row `metrics` showed `faithfulness: null` and
`answer_relevancy: null` across all items. Only `retrieval_relevance` (0.0) and
`latency_p95_ms` (694) were populated.

## Root cause

`execute_eval_run()` in the internal-write-api factory path passed `judge=None`
and `llm=None` to `run_golden_eval()` even when `VECINITA_MODAL_LLM_URL` was
configured on the DO app.

Per `packages/eval/vecinita_eval/runner.py`, faithfulness and answer relevancy
are only scored when a judge client is present. With `llm=None`, every row
returned the abstention copy ("I don't have enough community corpus context…")
even when retrieval returned URLs.

## Fix

- Added `packages/eval/vecinita_eval/modal_llm.py`:
  - `ModalHttpLLM` — LlamaIndex adapter over `vecinita-llm` HTTP client
  - `default_eval_runtime()` — builds shared judge + LLM from
    `VECINITA_MODAL_LLM_URL`
- Updated `execute_eval_run()` to resolve default judge/LLM when not injected
  (mirrors `_default_embed_fn` pattern; per ADR-033 and factory-app-env-deps)

## Repro test

`tests/bugs/test_bug_2026_07_01_eval_null_judge_metrics.py`

## Verification

- [x] Layer 1 — unit/bug tests green
- [ ] Layer 2 — re-trigger eval on staging after deploy; faithfulness/answer_relevancy non-null for non-abstain rows
- [ ] Layer 4 — production/staging UI shows numeric scores

**Note:** Rows with `retrieval_expectation` of `abstain` or `empty` intentionally
skip faithfulness scoring (by design in runner).

## Spec conformance

- `[Spec: docs/adr/ADR-033]` — eval runner uses HTTP LLM at `VECINITA_MODAL_LLM_URL`
- `[Spec: docs/deployment-integration.md §EV-008]` — same LLM endpoint as ChatRAG
