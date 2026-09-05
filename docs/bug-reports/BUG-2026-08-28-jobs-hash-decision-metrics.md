# BUG-2026-08-28 — GET /jobs 500 when freshness metrics include hash_decision

> Status: **fixed** (Modal redeployed 2026-08-28; live GET /jobs 200)  
> Feature: **F79** freshness / **F32** Jobs list  
> Component: `packages/shared-schemas` `JobMetrics`, Modal `vecinita-data-management`

## Error description

Live admin Jobs tab / `GET /jobs` on Modal returned **500 Internal Server Error** when the
job store contained a completed `freshness_refresh` job whose `metrics` include
`hash_decision` (e.g. `skip_rechunk`).

Initial EV-032 live probe saw **401** with only `X-Vecinita-Proxy-Key`. Admin FE also
sends a Supabase Bearer token; with both headers, auth succeeded and the **500** surfaced.

## Error logs

```text
pydantic_core._pydantic_core.ValidationError: 1 validation error for Job
metrics.hash_decision
  Extra inputs are not permitted [type=extra_forbidden, input_value='skip_rechunk', input_type=str]
  File ".../store.py", line 380, in job_record_to_schema
    return Job.model_validate(payload)
```

## Root cause

`freshness_refresh.py` writes `metrics.hash_decision` (`skip_rechunk` / `rechunk`), but
`JobMetrics` had no such field and `extra="forbid"`.

## Fix

- Added `hash_decision: Literal["skip_rechunk", "rechunk"] | None` to `JobMetrics`
- OpenAPI `JobMetrics` updated
- Live GET /jobs probes use Supabase JWT + proxy key
- Modal `vecinita-data-management` redeployed 2026-08-28

## Repro test

- `tests/bugs/test_bug_2026_08_28_jobs_hash_decision_metrics.py`
- TDD: red → green; live JWT probe PASS after deploy

## Interview record

| Field | Answer |
|-------|--------|
| Root cause confirm | Option 1 — add field + redeploy (2026-08-28) |
| Prod ack | Hotfix from EV-032 live smoke |

## Prevention

- Keep `JobMetrics` in sync with worker-written metric keys (F78–F80).
- Live Modal job probes must send JWT (admin FE parity).
