# Evolve report — EV-012

**Title:** Unified Admin Jobs (F32/F36)  
**Session:** S013-unified-job-monitoring  
**Status:** completed  
**Completed:** 2026-07-29  
**Merge:** [PR #153](https://github.com/Math-Data-Justice-Collaborative/vecinita/pull/153) → `main` @ `6940770`

## Outcome

Admin Jobs is Modal-primary (`GET /jobs`, SSE `/jobs/events`, cancel/retry/delete) with Admin
UI list/detail, eval enqueue bridge, and soft-delete on eval runs. ADR-038 records the Modal
lifecycle / DO storage split. Phase 19 (M82–M85) gate PASS; Path A staging smokes PASS; DO
apps reset to `main`; H0ci green on merge SHA.

## Full summary

See [docs/sessions/S013-unified-job-monitoring/reports/evolve-summary.md](sessions/S013-unified-job-monitoring/reports/evolve-summary.md).
