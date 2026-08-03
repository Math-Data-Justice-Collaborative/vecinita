# 01-requirements — S025 / EV-023 (CI + release)

> Date: 2026-08-03  
> Mode: **delta** (Lean+build)  
> Features: **F62** (#182), **F63** (#103)  
> Epic: [#194](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/194)

## Phase 0 locks (user `1,1,1,1`)

| ID | Lock |
|----|------|
| S025-D4 | Both children in this cycle |
| S025-D5 | Husky: push=lint+units; commit=typecheck+security-scan+job-dispatch; format-check PR-only; stop hooks keep typecheck |
| S025-D6 | Release after DO CD; patch bump; annotated tag + GitHub Release; `[skip release]`; no floating tags; no semantic-release |
| S025-D7 | F62 + F63 allocated |
| S025-D8 | Proceed to 01 |

## Standing docs updated

| Doc | Delta |
|-----|-------|
| `docs/feature-list.md` | F62, F63 rows + detail sections |
| `docs/user-journeys.md` | UJ-067, UJ-068 |
| `docs/test-plan.md` | TC-208–215 + journey map |
| `docs/acceptance-criteria.md` | AC-CI1–CI5, AC-REL1–REL5 |
| `docs/decisions.md` | RD-264–RD-271 |
| `docs/decisions/evolve-decisions.md` | §Cycle EV-023 |

## Connectivity / UI

**N/A** — no browser UI, no CORS/VITE changes. H4–H5 / Playwright not required for these Fn.

## Test strategy (for 07)

| Layer | Coverage |
|-------|----------|
| Unit | Hook script contracts (TC-208–211); release bump/skip/idempotent (TC-212–214); workflow structure (TC-215) |
| API e2e / Playwright | Not applicable (no product routes/UI) |
| Live (13) | First main merge after ship creates a tag (or `[skip release]` on docs-only) |

## Out of scope (AC-CI5 / AC-REL5)

lint-staged; format-check on commit; #181; replace GH CI; semantic-release; floating tags; pre-CD tagging.

## Next

02-verify-plan consistency check → Gate A→B → 07-build (04 skipped).
