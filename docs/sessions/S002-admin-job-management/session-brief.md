# S002 — Admin Job Management

- **Session ID:** S002-admin-job-management
- **Type:** feature (evolve) + embedded bug fix
- **Branch:** `feat/S002-admin-job-management`
- **Opened:** 2026-06-26
- **Orchestrator:** 16-evolve (evolve-lite routing)

## Intent

Make data-management jobs resilient and observable from the admin dashboard.

Two GitHub issues, handled together in one combined session:

- **#88 (bug / hotfix):** Ingest/retag jobs fail entirely when the `vecinita-llm`
  tagging call returns an empty / non-JSON completion
  (`LlmTagClientError: tag response is not valid JSON: Expecting value: line 1 column 1 (char 0)`).
  Tagging is best-effort, so a tag-inference failure must degrade gracefully (ingest the
  document with no LLM tags) instead of marking the whole job `failed`.
- **#89 (feature / evolve):** Admin dashboard has no Job Management view. Job status lives
  only in `JobForm` local state on the `/corpus` route, so navigating away unmounts it and
  drops the running/failed job info (same class as #53). Add a Job Management tab backed by
  a new list-jobs API.

## Scope

**#88 — graceful tag degradation (bug-investigation TDD)**
- `packages/tagging/vecinita_tagging/llm_client.py` — `_parse_tag_slugs` / `infer_document_tags`.
- `apps/data-management-backend/vecinita_data_management_backend/pipeline.py` —
  `run_ingest_job` continues with `tags=None` on tag-inference failure; document/chunks/embeddings
  still written and job `completes`.
- Repro test + bug report per `bug-investigation.mdc`.

**#89 — Job Management tab (full scope)**
- Backend: `GET /jobs` (newest first, optional `status` filter) in `app.py`; `list_jobs()` on
  `JobStore` / `DictJobStore` / `InMemoryJobStore`; OpenAPI contract update.
- Frontend: new `/jobs` route + nav item in `AdminLayout`; `JobsPage` listing jobs with status
  badges + error code/message + timestamps + poll; lift active-job tracking so navigation no
  longer drops jobs; en/es i18n.

## Out of scope

- No PII in job listings (ADR-004).
- No persistent server-side chat/session state changes.

## Issues

- https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/88
- https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/89
