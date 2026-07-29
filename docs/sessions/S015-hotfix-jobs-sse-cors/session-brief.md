# S015 — Hotfix: Jobs SSE CORS headers

| Field | Value |
|-------|--------|
| **Type** | hotfix |
| **Intent** | Restore admin Jobs live SSE (`GET /jobs/events`) blocked by CORS preflight |
| **Bug** | [BUG-2026-07-29-jobs-sse-cors-headers](../../bug-reports/BUG-2026-07-29-jobs-sse-cors-headers.md) |
| **Branch** | `fix/S015-jobs-sse-cors` |
| **Interview** | Production admin; list/poll OK; “Live updates unavailable”; Network on `/jobs/events` |

## Scope

- Allow browser SSE request headers (`Cache-Control`, `Last-Event-ID`) on Modal data-management CORS.
- Repro under `tests/bugs/`; Modal redeploy after user approval.

## Out of scope

- Jobs list polling redesign; eval-run SSE on write-api; new Jobs features.
