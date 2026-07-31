# BUG-2026-07-31 — Modal `job_type=eval` falls through to ingest

**Status:** open  
**Severity:** medium — Admin Evaluation enqueue creates a Modal job that always fails  
**Feature:** F36 / EV-012 — Modal `job_type=eval` (AC-J1, TC-124, ADR-038)  
**Session:** S018-eval-job-dispatch  
**Reported:** 2026-07-31  
**Environment:** Staging + production (Admin Evaluation → Modal data-management)

## Error description

Admin Evaluation can **enqueue** a Modal job with `job_type=eval`, but the Modal worker’s
`run_job` never handles that type. The dispatcher only covers backfill / retag / rebuild;
anything else (including `eval`) goes to ingest. An eval job has no URLs → empty batch upsert
→ `BatchUpsertRequest(documents=[])` ValidationError → job **failed**.

Path A workaround used for F36 (shadow eval): operator-local `execute_eval_run` against
staging DB, not Admin Evaluation → Modal.

**Secondary (included):** default `top_k=5` + 256-token chunks blew past vLLM
`max_model_len=2048`; staging drill used `top_k=2`.

## Error logs

```text
# From jobs.py dispatch (eval → else → run_ingest_job)
# ingest builds documents=[] then:
BatchUpsertRequest(documents=[])
→ pydantic ValidationError (documents min_length / empty batch)
→ store status=failed, error_code=ValidationError
```

S017 deploy-smoke advisory:

> Modal `job_type=eval` dispatch gap: `run_job` falls through to ingest →
> `BatchUpsertRequest(documents=[])` ValidationError.

## Symptoms & reproduction

| Field | Answer |
|-------|--------|
| Symptom | Eval Modal job fails immediately after enqueue |
| Where | Admin Evaluation → Modal `POST /jobs` → `run_job` |
| When | Every Admin Evaluation enqueue (not Path A local execute) |
| Frequency | Every time |
| Repro env | Both staging + production |
| Severity | Medium |
| Evidence | Code path in `jobs.py` + S017 deploy-smoke |

## Interview record (Phase 0)

| Field | Answer |
|-------|--------|
| Intent | New bug — open session + fix |
| Environment | Both (staging + production) |
| Severity | Medium |
| Path | A — wire `run_job` → eval worker |
| Secondary top_k | Include in this hotfix |

## Investigation

| # | Hypothesis | Result |
|---|------------|--------|
| H1 | `enqueue_eval` never creates Modal jobs | **Ruled out** — `DataManagementJobsClient.enqueue_eval` POSTs `job_type=eval` |
| H2 | `run_job` missing `eval` branch → ingest | **Confirmed** — elif chain has no `eval`; else → `run_ingest_job` |
| H3 | Empty ingest upsert ValidationError | **Confirmed** — `urls=[]` → `documents=[]` → `BatchUpsertRequest` fails |
| H4 | Eval execution should live on Modal with DATABASE_URL | **Rejected** — ADR-007 forbids `DATABASE_URL` on Modal workers |
| H5 | Modal should call DO write-api to execute eval | **Chosen** — Modal owns lifecycle; DO runs `execute_eval_run` (metrics SoT) |
| H6 | Synthesis prompt exceeds `max_model_len=2048` at top_k=5 | **Confirmed** (S017 drill); truncate synthesis context |

## Root cause

`run_job` has no `job_type == "eval"` arm. Eval jobs are treated as ingest. Separately,
eval synthesis builds unconstrained context from all retrieved chunks, which exceeds pinned
vLLM context at default `top_k=5` with 256-token chunks.

## Spec conformance

| Check | Result |
|-------|--------|
| ADR-038 Modal owns eval job lifecycle | Enqueue yes; worker dispatch **missing** |
| ADR-007 no DATABASE_URL on Modal | Execute via write-api HTTP |
| AC-J1 / TC-124 / UJ-044 | Eval jobs must complete, not fail as ingest |

## Repro test

- Path: `tests/bugs/test_bug_2026_07_31_eval_job_dispatch.py`
- Assert: `run_job` for `job_type=eval` completes via `execute_eval_run`, never empty ingest upsert.

### TDD iteration log

| # | Date | Action | Result |
|---|------|--------|--------|
| 1 | 2026-07-31 | Add unit repro for eval dispatch | **RED** — ValidationError `documents` too_short |
| 2 | 2026-07-31 | Wire `run_eval_job` + DO `/execute` + synthesis truncate | **GREEN** |

## Fix

1. `jobs.py`: `job_type == "eval"` → `run_eval_job`
2. `pipeline.run_eval_job`: Modal lifecycle + `InternalWriteClient.execute_eval_run`
3. Write-api `POST /internal/v1/eval/runs/{run_id}/execute` → `execute_eval_run` (ADR-007: no DB URL on Modal)
4. Forward adhoc `question` via `JobOptions.question` / enqueue body
5. Truncate eval synthesis context (`DEFAULT_SYNTHESIS_CONTEXT_MAX_CHARS=3500`) for `max_model_len=2048`

## Prevention & countermeasures

*(pending Phase 5)*
