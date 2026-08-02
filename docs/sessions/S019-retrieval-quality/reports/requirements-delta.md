# 01-requirements delta — EV-016 / F42

> **Session:** S019 · **Cycle:** EV-016 · **Date:** 2026-08-01  
> **Status:** completed

## Scope

**F42 = H7+P1 on E0** (S019-D31/D37). E1/#159 not shipped.

## Document Manifest (S019-D38)

| Document | Action |
|----------|--------|
| Feature List | F42 section + summary row |
| Spec | ChatRAG algorithm + query path + Shared RAG |
| User Journeys | UJ-001 amend; UJ-055; UJ-056 |
| Test Plan | TC-170–175 |
| Config Spec | `VECINITA_RAG_*` knobs |
| Acceptance Criteria | AC-RQ1–RQ7 |
| API Contract | skipped |

## Decisions

| ID | Choice |
|----|--------|
| S019-D38 | Manifest: mandatory + config + AC; skip API |
| S019-D39 | H7 default on; P3 via `packer=p3`; E0 embed |
| S019-D40 | UJ-055/056; TC-170–175; Hy1 ship 0.28/0.91 |
| S019-D41 | Env knobs for multi-query + packer + max chars |

## Next

`02-verify-plan` consistency audit → gate A→B → `04-tech-plan`.
