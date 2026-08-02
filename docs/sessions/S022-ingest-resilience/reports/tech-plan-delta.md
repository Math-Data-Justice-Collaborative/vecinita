# 04-tech-plan delta — EV-019 / F47–F49

> **Session:** S022 · **Cycle:** EV-019 · **Date:** 2026-08-02  
> **Status:** completed — Gate B→C PASS (S022-D22); 07-build started

## Approvals

| Choice | Result |
|--------|--------|
| TP1–TP6 (phase/milestones, ADR, schema, tests, deploy/deps, connectivity) | **Approved** (user option 1) |
| Phase 24 M101–M104 | Drafted into execution-plan |
| New ADR | None (reuse ADR-044) |
| Dependency / data-mgmt / deploy topology | Skipped (TP5); Path A + Path B escalate if F49 re-chunk |
| Admin FE / Playwright | Skipped unless knobs ship (M5 / TP4) |

## Artifacts

| Artifact | Path |
|----------|------|
| Execution plan Phase 24 | `docs/sessions/S000-internal-docs-archive/execution-plan.md` |
| Session roadmap | `docs/sessions/S022-ingest-resilience/roadmap.md` |
| This report | `docs/sessions/S022-ingest-resilience/reports/tech-plan-delta.md` |

## Milestones

| M | Focus | Fn |
|---|-------|-----|
| M101 | content_hash skip + ingest `force` + OpenAPI prose | F47 |
| M102 | Embed sub-batch + retry (batch 32 / retries 3 / backoff 0.5s) | F48 |
| M103 | HF tokenizer + `chunk_overlap_tokens` (default 32) | F49 |
| M104 | UJ-062 e2e + job metrics + phase-gate docs | F47–F49 |

## Locked defaults (carry)

| ID | Value |
|----|--------|
| Order (TP1 / RD-220) | M101 → M102 → M103 → M104 |
| Embed knobs (M1) | batch **32**, retries **3**, backoff **0.5s** |
| Overlap (RD-223) | **32** tokens |
| Tokenizer (ADR-044) | HF for `BAAI/bge-small-en-v1.5` |
| Fail policy (RD-222) | Fail URL after embed retry exhaust; dim mismatch hard-fail |
| Metrics (M2) | `skipped_unchanged`, `urls_failed_embed` — finalize in M104 |
| Deploy | Path A; Path B if live re-chunk required |

## Next

`07-build` (05/06 skipped) @ T101.1 — F47 content_hash skip.
