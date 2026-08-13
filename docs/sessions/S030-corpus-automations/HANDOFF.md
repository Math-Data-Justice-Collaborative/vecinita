# HANDOFF — S030-corpus-automations

**Updated:** 2026-08-13  
**Session:** S030-corpus-automations (`feature`)  
**Cycle:** EV-027 · F75 F76 F77  
**Branch:** `evolve/EV-027-corpus-automations`  
**Tip:** local ahead of origin (`0411feb`+)  
**Issues:** #73 · #72 · #219  

## Position

- **13-deploy-smoke** COMPLETE PASS — `passed_baseline_only`
- **15-service-health** COMPLETE **PASS** — `reports/service-health.md`
- Live stack healthy; EV-027 **not** cut over; flags **off**
- PR [#238](https://github.com/Math-Data-Justice-Collaborative/vecinita/pull/238) open
- Next: AskQuestion — close cycle / ship-path / other

## Decisions

| ID | Choice |
|----|--------|
| S030-D60 | Baseline live smoke only; flags off |
| S030-D61 | Accept H2 alembic tip-drift |
| S030-D62 | Continue to 15-service-health |
| S030-D63 | Recommended post-baseline health package |

## Reports

- `reports/deploy-smoke.md`
- `reports/service-health.md`
- `reports/deploy-checklist.md`

## Next

Await close / ship-path AskQuestion (or `@.cursor/skills/16-evolve/SKILL.md` for cycle close).
