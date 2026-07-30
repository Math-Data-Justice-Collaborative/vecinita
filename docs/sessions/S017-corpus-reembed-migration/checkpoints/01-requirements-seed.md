# 01-requirements seed — S017 / EV-015 (#167 / F41)

Generated from Phase 0 + 01 interview (2026-07-30). Locked decisions are **confirm-only**.

## Locked decisions (confirm)

See `docs/decisions/evolve-decisions.md` §Cycle EV-015 — S017-D1…D17; RD-188–RD-196.

Highlights:

- **F41** — Document store + corpus rebuild (single Fn)
- Modes: `reembed` | `rechunk` | `rescrape` via `job_type=rebuild`
- Ops: prefer **store-backed** reembed/rechunk; **no live scrape** unless explicit rescrape
- Dry-run: **shadow dual-write** + promote after F36
- Scope: whole corpus + optional `document_ids`; **force** bypasses hash-skip
- Version stamps + revision history; dim dual-write deferred to #159
- Retag separate; progress via Jobs SSE/detail only
- Store: Postgres `body_text` + `document_revisions` (ADR-040)
- Routing: **Standard+build**
- Prod: runbook only (no live prod rebuild in EV-015)

## Document manifest (delta) — written

| Document | Status |
|----------|--------|
| `docs/feature-list.md` | F41 done |
| `docs/user-journeys.md` | UJ-053, UJ-054 |
| `docs/test-plan.md` | TC-161–168 |
| `docs/acceptance-criteria.md` | AC-RB1–10 |
| `docs/spec.md` | F41 delta |
| `docs/api-contract.md` | rebuild + promote |
| `docs/config-spec.md` | rebuild/shadow/model id |
| `docs/adr/ADR-040-*.md` | accepted |
| `docs/decisions.md` | RD-188–196 |
| Session reports | 01-requirements + runbook outline |

## Open questions for 01 — resolved

All interview batches closed 2026-07-30.

## Proposed IDs (allocated)

- Fn: **F41** · UJ: **053–054** · TC: **161–168** · RD: **188–196** · AC: **RB1–10** · ADR: **040**
