# 01-requirements seed — S013 / EV-012 (#116)

Generated from Phase 0 intake (2026-07-28). Locked decisions are **confirm-only**.

## Locked decisions (confirm)

See `docs/decisions/evolve-decisions.md` §Cycle EV-012 — S013-D1…D22.

Highlights: Admin-only; extend F32/F36; v1+v2; Modal-primary Jobs list; `/jobs/:id`; SSE + poll fallback; #116 ACs + UJ-023; Lean+build.

## Document manifest (delta)

| Document | Action |
|----------|--------|
| `docs/feature-list.md` | Delta F32 + F36 |
| `docs/user-journeys.md` | Extend UJ-023; add detail/SSE/cancel as needed |
| `docs/test-plan.md` | TCs for Modal list, detail, SSE, cancel, retag document_id |
| `docs/acceptance-criteria.md` | Mirror #116 + SSE |
| `docs/api-contract.md` | Jobs events SSE; cancel/retry; retag metadata; eval events |
| `openapi/data-management.yaml` | Schema deltas |
| `openapi/internal-write.yaml` | Eval events / cancel if needed |
| `docs/adr/` | New ADR: jobs SoT + SSE transport |
| Session `reports/01-requirements-unified-jobs.md` | Stage report |

Skip greenfield templates (full spec rewrite, dependency inventory) unless open questions force them.

## Open questions for 01 interview

1. SSE failure: poll fallback interval / when to fall back?
2. Postgres vs modal.Dict SoT preference (informs ADR)?
3. Cancel/retry: admin-only vs viewer can cancel own?
4. Failed Modal job logs: dashboard deep-link vs function/call id copy?
5. Playwright T0-ui for Jobs list→detail navigation (skill default: yes)?

## Proposed RD range

RD-173+ (confirm against research-brief / last RD).
