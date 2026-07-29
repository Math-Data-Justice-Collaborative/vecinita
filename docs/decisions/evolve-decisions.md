# Evolve decisions

## Cycle EV-012 — Scope (S013 / #116)

**Approved:** 2026-07-28  
**Session:** S013-unified-job-monitoring  
**Issue:** https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/116

### Scope summary

Admin Dashboard unified job monitoring (not ChatRAG). **Modal** owns lifecycle for all
long-running admin jobs (ingest/retag/eval/future) via Modal job queue; Admin Jobs list is
Modal `GET /jobs`. **DO Postgres** is SoT for storage including eval metrics; **Supabase =
auth only**. Detail at `/jobs/:id`; SSE + 4s poll fallback; admin-only full job CRUD; Modal
log affordances on failure. Extend F32/F36; no new Fn. See ADR-038, RD-173–RD-178.

### Decisions (intake + 01)

| ID | Topic | Choice |
|----|-------|--------|
| S013-D1 | S012 artifacts | Leave uncommitted |
| S013-D2 | Scope | v1 + full v2 |
| S013-D3 | Feature identity | Extend F32/F36; no new Fn |
| S013-D4 | Success | Issue #116 ACs as written |
| S013-D5 | v2 items | All: SoT alignment, Modal logs, cancel/retry (+ delete) |
| S013-D6 | Detail UX | `/jobs/:id` |
| S013-D7 | Eval row | Summary + link to eval drill-down |
| S013-D8 | List source | **Amended:** Modal `GET /jobs` primary (not FE dual-list merge) |
| S013-D9 | Out of scope | ChatRAG UI; Langfuse UI not in scope; all long-running admin jobs IN |
| S013-D10 | API risk | Compatible/additive |
| S013-D11 | Privacy | F32 limits; no PII |
| S013-D12 | Cycle size | One cycle EV-012 |
| S013-D13 | Apps | Admin FE + Modal DM + internal-write |
| S013-D14 | Env/secrets | Prefer none new |
| S013-D15 | CORS/VITE | Same Admin SPA |
| S013-D16 | UI preview | Yes — local non-deployed when useful |
| S013-D17 | Job updates | SSE + 4s poll fallback + SSE retry (RD-173) |
| S013-D18 | Acceptance | #116 ACs + extend UJ-023 |
| S013-D19 | E2E | API e2e + Vitest + Playwright T0-ui; live T3 after deploy |
| S013-D20 | Scope approval | Proceed |
| S013-D21 | Preset | Lean (superseded by D22) |
| S013-D22 | Routing | **Lean+build** |
| RD-174 | Job host | Modal for all long-running jobs incl. eval (amend ADR-033) |
| RD-175 | Storage/auth | DO Postgres storage SoT; Supabase auth-only |
| RD-176 | CRUD | Admin-only full job CRUD |

### Architecture amendment (01-requirements)

See ADR-038 and `docs/decisions.md` RD-173–RD-178.
