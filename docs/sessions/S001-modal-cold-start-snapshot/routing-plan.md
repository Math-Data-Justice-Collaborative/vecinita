# S001 — Routing plan

> Type: ops (performance spike). Approved: 2026-06-25.

This is a **timeboxed spike**, not a feature build. The plan is instrument → decide → (maybe)
implement → measure → deploy. The snapshot rewrite only proceeds if the instrumentation gate
passes.

| Stage | Run? | Rationale |
|-------|------|-----------|
| 00-context | ✅ done | This brainstorm + plan/ADR (current) |
| 01–06 (requirements/tech plan) | ⏭️ skip | No new product feature; perf change to existing service under ADR-009 |
| 07-build / build-executor | ✅ | Two phases: (P1) instrumentation; (P2) snapshot impl — gated on P1 result |
| 08-verify-build | ✅ | Lint/typecheck/test the Modal app + any client changes |
| 09-qa | ⏭️ optional | Only if client-facing code changes |
| 10-e2e | ⏭️ skip | No new user journey |
| 13-deploy-smoke | ✅ | Snapshots only generate on **deployed** apps; measure cold start in staging |
| 15-service-health | ✅ | Confirm cold-vs-warm ask latency post-change; record actuals |

## Decision gate (between P1 and P2)

After P1 instrumentation produces a cold-start time breakdown:

- **Compilation/init dominates** (e.g. CUDA graph capture + torch import > weight load) →
  proceed to P2 snapshot spike.
- **Weight load dominates** → **abort snapshot**, fall back to budget-safe combo
  (`enforce_eager=True`, pre-warm on session open, raise `scaledown_window`), update ADR-022 to
  Rejected/Superseded.

## Skip rationale

Requirements/tech-plan stages are skipped because this modifies an already-specced service
(ADR-009) for performance only; no contract, schema, or journey changes. If the snapshot work
forces a model or GPU-tier change, re-open the relevant stage.
