# S018 — Deploy smoke (Admin Evaluation eval dispatch)

**Date:** 2026-07-31  
**Merge SHA:** `a6c39e57e856e75d149b1ac1af82d6e92243af19` (PR #169)  
**Bug:** BUG-2026-07-31-eval-job-dispatch  
**Result:** **PASS**

## CD chain

| Step | Run | Conclusion |
|------|-----|------------|
| CI | [30633805272](https://github.com/Math-Data-Justice-Collaborative/vecinita/actions/runs/30633805272) | success |
| Deploy preflight | [30634041609](https://github.com/Math-Data-Justice-Collaborative/vecinita/actions/runs/30634041609) | success |
| Deploy Modal | [30634088059](https://github.com/Math-Data-Justice-Collaborative/vecinita/actions/runs/30634088059) | success |
| Deploy DigitalOcean | [30634163306](https://github.com/Math-Data-Justice-Collaborative/vecinita/actions/runs/30634163306) | success |

DO note: workflow `success` returned while write-api was still **BUILDING**. Live `/execute` appeared ~1–2 min later (`401` without auth → OpenAPI lists route). Active deployment cause=`manual` @ `2026-07-31T13:22:44Z`.

## Live checks

| Check | Result |
|-------|--------|
| Write-api `/health` | 200 |
| Modal DM `/health` | 200 |
| Admin FE | 200 |
| OpenAPI `POST /internal/v1/eval/runs/{run_id}/execute` | present after DO build ACTIVE |
| Adhoc Admin Evaluation enqueue → Modal `job_type=eval` | **PASS** |

## Smoke run (adhoc)

| Field | Value |
|-------|--------|
| `run_id` | `eb76b740-4aa5-4977-b519-0b133cd48b5c` |
| Modal `job_id` | `d0a9f39c-df25-445f-87ac-9e07a1c7429d` |
| Body | `mode=adhoc`, staging corpus, `top_k=2`, `max_tokens=128` |
| Modal status | `pending` → `running` → **`completed`** (`error_code=null`) |
| Eval status | `pending` → **`completed`** |
| Items | 1 (`retrieval_pass=true`) |
| Metrics | retrieval_relevance=1.0; faithfulness=0.0; answer_relevancy=0.0; latency_p95_ms=8145 |

### Regression contrast

Pre-fix Modal eval jobs failed immediately with:

```text
ValidationError … BatchUpsertRequest documents List should have at least 1 item
```

This smoke: no ingest fall-through; Modal stayed on `job_type=eval` and completed via DO `/execute`.

## Verdict

Infra + Admin Evaluation path for S018: **PASS**. Bug remains open until Phase 5 prevention interview.
