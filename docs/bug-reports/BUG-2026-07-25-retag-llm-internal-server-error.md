# BUG-2026-07-25 — Manage Tags LLM retag returns Internal Server Error

> Status: **fix applied (local)** — awaiting PR / staging deploy
> Issue: **#146**
> Session: **S011-hotfix-retag-empty-chats**
> Feature: **F20** (LLM auto-tagging) / Manage Tags retag
> Component: `apps/internal-write-api` → Modal `vecinita-data-management` `/jobs`

## Error description

In the admin **Manage Tags** UI, **LLM re-tag** returns:

```json
{"detail":"Internal Server Error"}
```

instead of enqueueing a retag job (or a clear 4xx/502).

## Error logs

### Staging live repro (2026-07-25)

```text
POST https://vecinita-internal-write-api-icze4.ondigitalocean.app/internal/v1/documents/{id}/retag
Authorization: Bearer <admin JWT | INTERNAL_API_KEY>
→ 500 {"detail":"Internal Server Error"}
```

Modal data-management direct:

```text
POST …/jobs  + X-Vecinita-Proxy-Key only     → 401 {"detail":"Unauthorized"}
POST …/jobs  + X-Vecinita-Proxy-Key + JWT    → 202 {"job_id":"…","status":"pending"}
```

## Symptoms & reproduction

| Field | Value |
|-------|-------|
| Symptom | Immediate HTTP 500 on LLM retag from Manage Tags |
| Where | Staging admin → internal-write-api → Modal data-management |
| When | Confirmed 2026-07-25 (post F34 JWT on `/jobs*`) |
| Frequency | Every time |
| Severity | High — retag unusable from admin |
| Evidence | Live staging calls above |

## Interview record

| Decision | Choice |
|----------|--------|
| Bugs | #146 then #145 |
| Session | Close S010, open S011 hotfix |
| Deploy | Fix + staging smoke after merge |

## Remediation path

**local-first** — fix in repo, PR, then staging smoke after merge (S011-D3).

## Investigation

| # | Hypothesis | Result |
|---|------------|--------|
| H1 | Write API `DataManagementJobsClient` not configured → 503 | **Rejected** — would be 503 "not configured"; we get 500 |
| H2 | Modal `/jobs` rejects proxy-key-only (needs admin JWT after F34) | **Confirmed** — proxy-only 401; proxy+JWT 202 |
| H3 | Write API `enqueue_retag` does not forward `Authorization` | **Confirmed** — jobs_client sent only `X-Vecinita-Proxy-Key` |
| H4 | Uncaught `DataManagementJobsClientError` becomes opaque FastAPI 500 | **Confirmed** — retag handlers did not catch enqueue errors |

### Root cause

Write API enqueued Modal retag with **proxy key only**. Modal `POST /jobs` uses `write_auth_dep` (proxy key **and** admin JWT via `require_admin`). Modal returned **401**; write API raised `DataManagementJobsClientError` uncaught → **500 Internal Server Error**.

## Repro test

| Test | Path | Status |
|------|------|--------|
| Retag maps Modal enqueue 401 to 502 + forwards Authorization | `tests/bugs/test_bug_2026_07_25_retag_llm_internal_server_error.py` | red → green (2026-07-25) |

### TDD iteration log

| # | Date | Action | Result |
|---|------|--------|--------|
| 1 | 2026-07-25 | Write repro asserting no opaque 500 + Authorization forward | RED (500; auth=None) |
| 2 | 2026-07-25 | Forward Authorization; map JobsClientError → `HTTP_BAD_GATEWAY` | still RED — Starlette has no `HTTP_BAD_GATEWAY` |
| 3 | 2026-07-25 | Use `status.HTTP_502_BAD_GATEWAY` | GREEN |

## Fix

1. **`jobs_client.enqueue_retag(..., authorization=)`** — forward caller `Authorization` with proxy key.
2. **`retag_document` / `bulk_retag`** — pass `Request.headers["Authorization"]`; catch `DataManagementJobsClientError` → **502** with enqueue detail.

## Verification plan

- Success: Manage Tags LLM retag returns `job_id` with admin JWT; failures are clear 502 not opaque 500
- Checks: bug repro + jobs_client / bulk unit tests green
- Post-merge: staging smoke (15-service-health) — DO internal-write-api redeploy required

## Spec conformance

- [Corpus: api] F34 admin JWT on Modal `/jobs*`
- [Corpus: product] F20 LLM tagging / retag
