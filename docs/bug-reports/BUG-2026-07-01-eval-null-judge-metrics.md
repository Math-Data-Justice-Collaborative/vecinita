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

Two compounding issues:

1. **Empty retrieval (primary for run `51b99266…`):** Every row returned
   `retrieved_urls: []` and `retrieval_relevance: 0.0`. The eval runner queries
   the staging `DATABASE_URL` pgvector corpus; fixture golden rows do not embed
   documents by themselves. Without seeded eval corpus chunks, retrieval fails and
   the RAG path returns abstention copy.

2. **Judge gating (code, fixed locally):** `run_golden_eval()` only scored
   faithfulness and answer relevancy when `chunks` was non-empty. Even with
   `VECINITA_MODAL_LLM_URL` wired via `default_eval_runtime()`, LlamaIndex
   **AnswerRelevancyEvaluator** never ran on zero-chunk rows. Faithfulness
   correctly requires retrieved context.

3. **Prior factory wiring gap (fixed, may need deploy):** `execute_eval_run()`
   previously passed `judge=None` / `llm=None` when not injected, even if
   `VECINITA_MODAL_LLM_URL` was set on internal-write-api.

## Fix

- `packages/eval/vecinita_eval/modal_llm.py` — `default_eval_runtime()` wires judge + LLM
- `execute_eval_run()` — resolves default judge/LLM when not injected
- `run_golden_eval()` — score **answer relevancy** whenever judge is wired and
  answer text exists; keep **faithfulness** gated on non-empty chunks
- Admin UI — drill-down shows model answer column, wrap toggle, column picker
  (persisted in `localStorage`); hint when judge metrics absent with 0% retrieval

## Repro test

- `tests/bugs/test_bug_2026_07_01_eval_null_judge_metrics.py`
- `tests/unit/eval/test_runner_judge_contract.py` — CI contract (judge wiring, zero-chunk answer relevancy)
- `tests/unit/internal_write_api/test_eval_service.py` — default judge resolution + persisted judge metrics
- `tests/unit/internal_write_api/test_app_eval_routes.py` — factory `create_app()` judge wiring
- `tests/e2e/test_uj039_eval_run_trigger.py` — completed run must expose non-null judge metrics
- Vitest `test_evaluation_page.test.tsx` — drill-down renders scores + model answer

## Verification

- [x] Layer 1 — unit/bug tests green
- [ ] Layer 2 — re-trigger eval on staging after deploy; faithfulness/answer_relevancy non-null for non-abstain rows
- [ ] Layer 4 — production/staging UI shows numeric scores

**Note:** Rows with `retrieval_expectation` of `abstain` or `empty` intentionally
skip faithfulness scoring (by design in runner).

## Spec conformance

- `[Spec: docs/adr/ADR-033]` — eval runner uses HTTP LLM at `VECINITA_MODAL_LLM_URL`
- `[Spec: docs/deployment-integration.md §EV-008]` — same LLM endpoint as ChatRAG
