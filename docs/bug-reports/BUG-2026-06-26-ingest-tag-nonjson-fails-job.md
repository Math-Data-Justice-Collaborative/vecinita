# BUG-2026-06-26 — Ingest/retag job fails when LLM tag response is not valid JSON

> Status: **fix applied (local)**
> Issue: **#88**
> Session: **S002-admin-job-management**
> Feature: **F7** (batch ingest), **F20** (LLM auto-tagging at ingest)
> Component: `apps/data-management-backend/vecinita_data_management_backend/pipeline.py`,
> `packages/tagging/vecinita_tagging/llm_client.py`

## Error description

A data-management ingest job fails entirely when the `vecinita-llm` tagging call returns an
empty / non-JSON completion. Tagging is a best-effort enrichment step, so a tag-inference
failure should degrade gracefully (ingest the document with no LLM tags) instead of marking
the whole job `failed`.

## Error logs

```text
Job 304c63b5-6524-4ce6-a35d-a2ea2950d477: failed

LlmTagClientError: tag response is not valid JSON: Expecting value: line 1 column 1 (char 0)
```

`Expecting value: line 1 column 1 (char 0)` = `json.loads` received an empty string — the
LLM returned an empty / non-JSON completion for the tag prompt.

## Symptoms & reproduction

| Field | Value |
|-------|-------|
| Symptom | Ingest job marked `failed`; document never written |
| Where | Staging (admin → Modal data-management → vecinita-llm) |
| When | When the LLM tag completion is empty / non-JSON |
| Frequency | Intermittent (depends on LLM output) |
| Severity | High — a transient empty completion drops the whole document |
| Evidence | Job 304c63b5-6524-4ce6-a35d-a2ea2950d477 failure |

## Remediation path

**local-first** — fix locally, deploy after user approval.

## Investigation

| # | Hypothesis | Result |
|---|------------|--------|
| H1 | `_parse_tag_slugs` raises `LlmTagClientError` on empty/non-JSON completion | **Confirmed** (llm_client.py:112-120) |
| H2 | `run_ingest_job` calls `infer_document_tags` inside the main `try` with no local handling, so the exception propagates and the broad `except Exception` marks the job `failed` | **Confirmed** (pipeline.py) |
| H3 | Document is fully ingestable without LLM tags (tags are optional) | **Confirmed** (DocumentUpsert.tags is optional) |

### Root cause

**Structural code bug**: tag inference was treated as a hard dependency of ingest. In
`run_ingest_job`, `tag_client.infer_document_tags(...)` ran inside the main try block with
no local `except`, so any `LlmTagClientError` (empty/non-JSON completion or wrapped
`LlmClientError`) aborted scrape → chunk → **tag** → embed → upsert and set the job `failed`,
even though the document, chunks, and embeddings were ready to write.

## Repro test

| Test | Path | Status |
|------|------|--------|
| Ingest completes when tag inference returns non-JSON | `tests/bugs/test_bug_2026_06_26_ingest_tag_nonjson_fails_job.py` | red → green |

### TDD iteration log

| # | Date | Action | Result |
|---|------|--------|--------|
| 1 | 2026-06-26 | Write repro: tag client raises `LlmTagClientError`; assert ingest job `completed` + document written without tags | RED: `LlmTagClientError` propagates from pipeline.py:90 |
| 2 | 2026-06-26 | Apply fix: wrap tag inference in `try/except LlmTagClientError`, log warning, degrade to no tags | GREEN |

## Fix

**`apps/data-management-backend/vecinita_data_management_backend/pipeline.py`** —
`run_ingest_job` now wraps `tag_client.infer_document_tags(...)` in `try/except
LlmTagClientError`. On failure it logs a warning (`tag inference failed for <url>; ingesting
without LLM tags`) and continues with `inferred = []`, so the document, chunks, and
embeddings are still written and the job `completes`. `tag_models` is only built when tags
were actually inferred.

Retag jobs (`run_retag_job`) intentionally keep failing on tag errors — tagging is the sole
purpose of a retag, so a failure there is a true terminal failure surfaced to the operator
(visible via the Job Management tab, #89).

## Verification

### Layer 1 — Automated

- [x] Repro test red → green
- [x] `tests/unit/data_management/test_pipeline.py` passes (no regression)
- [x] `ruff check` + `basedpyright` clean on changed files

### Layer 2 — Reproduction

- [x] Ingest job with non-JSON tag response now `completes` with the document written, no LLM tags

### Layer 3/4 — Pre-deploy / production

- [ ] Deploy to Modal data-management (after PR merge + user approval)
- [ ] 15-service-health follow-up

## Prevention & countermeasures

- Best-effort enrichment steps (tagging) must not fail the primary ingest pipeline.
- Failed jobs surface `error_code` + `error_message` in the new Job Management tab (#89).

## Timeline

| Event | Date |
|-------|------|
| User report | 2026-06-26 |
| Repro confirmed | 2026-06-26 |
| Fix applied | 2026-06-26 |
