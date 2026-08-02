# Phase 22 gate checklist — EV-017 / S020 (F43–F45)

> **Session:** S020-retrieval-batch-b · **Cycle:** EV-017  
> **Branch:** `evolve/EV-017-retrieval-batch-b`  
> **Date:** 2026-08-02  
> **ADR:** [ADR-042](../../../adr/ADR-042-in-process-h1-answer-cache.md)  
> **CE ship-gate template:** [ce-ship-gate.md](./ce-ship-gate.md) · **CE runbook:** [spike-f45-ce-runbook.md](./spike-f45-ce-runbook.md)

## Build complete (07-build / T2)

| Criterion | Status | Evidence |
|-----------|--------|----------|
| All M94–M98 tasks completed (T94.1–T98.4) | ✅ | execution-plan Phase 22 |
| TC-176–TC-183 green at T2 | ✅ | unit + `tests/e2e/test_uj057_*` / `uj058_*` / `uj059_*` |
| AC-BB1–AC-BB8, AC-BB10 at T2 | ✅ | mapped to TC-176–183 + defaults |
| `cache_hit` in OpenAPI + ask/stream | ✅ | T95.3–T95.4; OpenAPI check |
| Soft language + CE flags default **off** | ✅ | TC-181 / TC-183 |
| CE spike ephemeral Modal T4; ChatRAG ≠ playground | ✅ | T97.4 scripts + runbook (S020-D15) |
| No LangGraph; no durable volume cache; content-hash keys | ✅ | ADR-042 / ADR-004 |
| ruff / basedpyright clean on changed paths; e2e UJ-057–059 green | ✅ | local pytest 2026-08-02 |

## Deferred to 08 / Phase C PR / 12–13

| Criterion | Status | Notes |
|-----------|--------|-------|
| 08-verify-build | ✅ PASS (scoped) | [verification-report.md](./verification-report.md) @ `ccc82df`; DB suites → CI |
| TC-184 / AC-BB9 CE ship metrics | ⏳ staging | Fill [ce-ship-gate.md](./ce-ship-gate.md) from spike JSON |
| Path A deploy smoke (13) | ⏳ | After PR merge + deploy approval |

## Cross-links

| Artifact | Path |
|----------|------|
| ADR-042 | `docs/adr/ADR-042-in-process-h1-answer-cache.md` |
| Execution plan Phase 22 | `docs/sessions/S000-internal-docs-archive/execution-plan.md` |
| Session roadmap | `docs/sessions/S020-retrieval-batch-b/roadmap.md` |
| F45 CE Modal app | `docs/sessions/S020-retrieval-batch-b/scripts/spike_f45_ce_modal.py` |
| F45 CE harness | `docs/sessions/S020-retrieval-batch-b/scripts/spike_f45_ce_ship_gate.py` |

## Gate verdict (build)

**PASS at T2** for F43–F45 implementation + e2e. Staging CE ship evidence (AC-BB9) remains
open until spike metrics are recorded. Next: **08-verify-build** then Phase C PR.
