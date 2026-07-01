# BUG-2026-07-01 — Eval run fails immediately (Modal embed 404)

> Status: **fixing**  
> Feature: **F36** (admin RAG evaluation, EV-008)  
> Component: `apps/internal-write-api`, DO secrets, `data-management-frontend`

## Error description

Admin Evaluation page: **Run evaluation** returns quickly with `status: failed`, empty
`items[]`, and null `metrics_summary` fields. Example:

```json
{
  "run_id": "60784050-c141-4e71-9ac6-302c876e861e",
  "status": "failed",
  "metrics_summary": {
    "retrieval_relevance": null,
    "faithfulness": null,
    "answer_relevancy": null,
    "latency_p95_ms": null,
    "custom_scores": null
  },
  "items": []
}
```

## Error logs

DigitalOcean internal-write-api (`vecinita-internal-write-api`, 2026-07-01 ~22:11 UTC):

```text
vecinita_embedding_client.client.EmbeddingClientError: embed failed with status 404: modal-http: invalid function call
  File eval_service.py execute_eval_run → run_golden_eval → CorpusPgvectorRetriever → _default_embed_fn → EmbeddingClient.embed
```

Reproduced externally: POST to `https://fontface--vecinita-embedding-embedding-api.modal.run/embed`
returns `modal-http: invalid function call`. Correct URL
`https://vecinita--vecinita-embedding-embedding-api.modal.run/embed` returns **200**.

## Symptoms & reproduction

| Field | Value |
|-------|-------|
| Symptom | Wrong output — run fails with no per-row results |
| Where | Production (DO staging — admin Evaluation tab) |
| When | After EV-008 deploy; eval list routes fixed earlier same day |
| Frequency | Every time |
| Repro env | Production |
| Severity | High — eval feature unusable |
| Evidence | User JSON + DO logs |

## Root cause

**Config / infra:** `VECINITA_MODAL_EMBED_URL` on internal-write-api points at the wrong Modal
workspace prefix (`fontface--` instead of `vecinita--`). Background eval calls `/embed` on that
base URL → Modal 404 `invalid function call`.

**Implementation gap:** `eval_runs.error_message` was persisted on failure but not returned in
`GET /internal/v1/eval/runs/{id}`, so the UI showed only `failed` with no diagnostic text.

## Fix

1. **Code:** Expose `error_message` on eval run list + detail API; show alert on Evaluation page
   when `status=failed`.
2. **Ops:** Set DO secret `VECINITA_MODAL_EMBED_URL` to
   `https://vecinita--vecinita-embedding-embedding-api.modal.run` (no `/health` suffix) and
   redeploy internal-write-api.

## Repro test

- `tests/bugs/test_bug_2026_07_01_eval_run_error_message.py`
- `apps/data-management-frontend/src/test/test_evaluation_page.test.tsx` (failed run error alert)

## Verification plan

| Layer | Check |
|-------|-------|
| L1 | Bug repro tests + eval unit/integration green |
| L2 | User re-runs evaluation after DO secret fix |
| L4 | Run completes with non-empty items + metrics |

## Timeline

| When | Event |
|------|-------|
| 2026-07-01 ~22:11 UTC | User reports immediate eval failure (run 60784050…) |
| 2026-07-01 | DO logs → embed 404 invalid function call; wrong Modal workspace URL |
