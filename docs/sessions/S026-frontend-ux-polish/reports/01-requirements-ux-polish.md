# 01-requirements — EV-024 / S026 UX polish (#193)

**Session:** S026-frontend-ux-polish  
**Cycle:** EV-024  
**Date:** 2026-08-04  
**Features:** F64–F69  
**Preset:** Standard  
**Issues:** #193 epic; #87, #93, #104, #106, #186, #170

## Summary

Delta requirements for ChatRAG + Admin UX polish (one PR per issue). Phase 0C seed loaded;
intake S026-D1–D19 locked. Specs updated in standing docs; ADR-046 for anonymous feedback.

## Document deltas

| Document | Change |
|----------|--------|
| `docs/feature-list.md` | F64–F69 |
| `docs/user-journeys.md` | UJ-069–074 |
| `docs/test-plan.md` | TC-216–230 + journey map |
| `docs/acceptance-criteria.md` | AC-UX1–16 |
| `docs/api-contract.md` | `energy_estimate`; `POST /feedback`; admin/internal feedback; `actor_email` |
| `docs/config-spec.md` | Energy + feedback env knobs |
| `docs/decisions.md` | RD-272–285 |
| `docs/decisions/evolve-decisions.md` | §EV-024 |
| `docs/adr/ADR-046-*.md` | Anonymous feedback / ADR-004 amendment |
| `docs/adr/ADR-004-*.md` | Link to ADR-046 |

## Locked decisions (S026-D1–D19)

See evolve-decisions §EV-024 and seed. Highlights: no surveys; no visitor email; backend
energy heuristic + UI advisory; 6 PRs; Standard routing; Tooltip in `frontend-ui`.

## Test requirements (by layer)

| Fn | Unit / Vitest | API e2e | UI e2e | Privacy / integration |
|----|---------------|---------|--------|------------------------|
| F64 | Typed catalog | — | Playwright wait | — |
| F65 | Formula helper | ask + stream | Chip/advisory | — |
| F66 | ActionIcon | — | opt | — |
| F67 | Tooltip EN/ES | — | opt | — |
| F68 | Form UI | POST feedback | Feedback journey | Schema + reject email |
| F69 | Audit label UI | Enriched audit list | opt | audit_log PII-free |

## Next

02-verify-plan consistency audit on deltas; then Gate A→B → 04-tech-plan.
