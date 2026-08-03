# Deploy Smoke — S023 / EV-020 (F50–F51)

> **Generated**: 2026-08-03  
> **Status**: **in_progress** — blocked on operator credentials  
> **Path**: A — DO ChatRAG (`VECINITA_TOP_K=8`, `VECINITA_RAG_PACKER=p3`)  
> **PR**: [#180](https://github.com/Math-Data-Justice-Collaborative/vecinita/pull/180) — OPEN, CI green, MERGEABLE  
> **Tip**: `267af20` (+ uncommitted 11/12 session artifacts)  
> **Staging now**: `bd6bb00` (S022)

## Preconditions

| Check | Status |
|-------|--------|
| 12-verify-deploy | **completed** (S023-D21) |
| CI on PR | **PASS** |
| `prod.env` | **absent** |
| `doctl` | **not found** |
| H0c | **PASS** (preflight at 12) |

## Deploy log

| # | Step | Status | Notes |
|---|------|--------|-------|
| 1 | Commit session artifacts | pending | verify-impl, deploy-checklist, HANDOFF, … |
| 2 | Merge PR #180 / Path A redeploy | pending | needs user + credentials |
| 3 | H1–H3 API smoke | pending | |
| 4 | H4–H5 connectivity | pending | |
| 5 | Live TOP_K=8 / PACKER=p3 confirm | pending | AC-RQ8/RQ9 live |

## Blockers

1. No local `prod.env` for DO/Modal staging keys  
2. `doctl` not on PATH (manual DO ops unavailable in this environment)

Awaiting user deploy-path choice before continuing.
