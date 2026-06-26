# ADR-023: Job Management tab + best-effort ingest tagging

**Status:** Accepted (S002 — implemented and tested)
**Stage:** 00-context / 07-build (S002-admin-job-management)
**Date:** 2026-06-26
**Issues:** #88 (bug), #89 (feature)

## Context

Two related problems surfaced in the admin data-management system:

1. **#88** — Ingest/retag jobs failed entirely when the `vecinita-llm` tagging call returned an
   empty / non-JSON completion (`LlmTagClientError: tag response is not valid JSON: Expecting
   value: line 1 column 1 (char 0)`). Tagging is best-effort enrichment, yet a tag-inference
   failure aborted the whole scrape→chunk→tag→embed→upsert pipeline.
2. **#89** — Job status lived only in `JobForm`'s component-local React state on the `/corpus`
   route. Navigating to another tab unmounted it, wiping `activeJob` and stopping the poll, so
   operators lost all visibility of running/failed jobs (same class as #53). There was no
   list-jobs endpoint — only `POST /jobs` and `GET /jobs/{job_id}`.

## Decision

**#88 — Ingest tagging is best-effort.** `run_ingest_job` wraps `infer_document_tags` in
`try/except LlmTagClientError`; on failure it logs a warning and continues with no LLM tags, so
the document/chunks/embeddings are still written and the job `completes`. Retag jobs still fail
on tag errors (tagging is their sole purpose; the failure is surfaced via the Job Management tab).

**#89 — Server-backed Job Management tab.** Rather than lift `JobForm`'s local state into a shared
context/app shell, make job visibility **server-sourced**:

- New `GET /jobs` list endpoint (newest first, optional `?status=` filter) + `list_jobs()` on
  `JobStore` / `DictJobStore` / `InMemoryJobStore`. `job_type` added to the `Job` schema; new
  `JobList` response model; OpenAPI updated.
- New `/jobs` admin route + nav item + `JobsPage` that lists jobs from the server and polls.

Because the source of truth is the server (jobs persist in the shared `modal.Dict`), navigating
away and back simply re-fetches — the data-loss symptom disappears without app-shell state
lifting. This is simpler and more robust than client-state lifting and aligns with ADR-004
(chat history stays client-only; job metadata is non-PII operational state already on the server).

## Consequences

- A flaky/empty LLM tag completion no longer drops a document; tagging degrades gracefully.
- Operators get durable, cross-navigation job visibility (running/completed/failed + error code).
- `GET /jobs` is a new API surface (GET verb already CORS-allowed; no new preflight verb).
- No job cancellation/retry yet; status/type enums localized, error messages remain source-form
  (consistent with F31 R30). No PII in listings (URLs + status only).

## Alternatives considered

- **Lift `JobForm` state into the app shell / context** (like #53's `useChatHistory`): rejected —
  more invasive, still loses jobs on full reload, and duplicates state the server already holds.
- **Fail ingest on tag error but auto-retry**: rejected — adds latency/cost and still risks
  dropping the document; tagging is genuinely optional enrichment.
