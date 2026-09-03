# BUG-2026-09-03 — Opaque Internal Server Error on documents/batch

## Error description

Freshness rechunk called `POST /internal/v1/documents/batch` and received
`500 {"detail":"Internal Server Error"}` with no stable `error_code` and no
operator-visible exception type. Modal only saw the client-side wrapper message,
so root cause could not be confirmed when staging no longer reproduced the 500.

## Error logs

```
InternalWriteClientError: upsert_batch failed: 500 {"detail":"Internal Server Error"}
```

(Modal `vecinita-data-management`, 2026-09-02 ~19:57 EDT — see HF-freshness-upsert-batch-500)

## Investigation

| Time | Note |
|------|------|
| 2026-09-02 | Observed on prod-path freshness rechunk |
| 2026-09-03 | Staging hash-change refresh: batch **200** (not reproduced) |
| 2026-09-03 | Operator chose option 1: stable error detail + logging |

## Root cause

**Confirmed for this slice:** Uncaught exceptions in `batch_upsert` use FastAPI’s
default opaque 500 body. That blocks diagnosis of intermittent / env-specific
failures.

## Repro test

- Path: `tests/bugs/test_bug_2026_09_03_upsert_batch_opaque_500.py`
- Status: green (`tests/bugs` + `tests/unit/internal_write_api/test_batch_upsert_error_detail.py`)

## Fix

Wrap `POST /internal/v1/documents/batch` failures: `logger.exception` + HTTP 500
detail `{error_code, error_type}` (`batch_upsert_failed` /
`batch_upsert_integrity_error`).

## Citations

[Corpus: feature-list.md §F79]
[Spec: docs/api-contract.md §POST /internal/v1/documents/batch]
[Spec: docs/adr/ADR-052-corpus-automation-orchestration.md]
