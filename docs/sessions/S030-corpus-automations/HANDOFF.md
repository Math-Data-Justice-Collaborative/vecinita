# HANDOFF — S030-corpus-automations

**Updated:** 2026-08-13  
**Session:** S030-corpus-automations (`feature`)  
**Cycle:** EV-027 · F75 F76 F77  
**Branch:** `evolve/EV-027-corpus-automations`  
**Tip:** `fee4d12` (report); smoke CI @ `588dab6`  
**Issues:** #73 · #72 · #219  

## Position

- **13-deploy-smoke** **COMPLETE PASS** — `baseline_only_flags_off` (`passed_baseline_only`)
- Report: `reports/deploy-smoke.md`
- EV-027 **not** on live; flags off; enable/promote still gated
- PR [#238](https://github.com/Math-Data-Justice-Collaborative/vecinita/pull/238) open (no merge)
- Next: AskQuestion — 15-service-health / close / ship-path

## Decisions

| ID | Choice |
|----|--------|
| S030-D58 | Resume 12; staging_as_live; push+CI; checklist-only; F75–F77 scope |
| S030-D59 | Approve mitigations 1–4 + rollback; checklist **ready** (flags off) |
| S030-D60 | Baseline live smoke only; push tip; flags off; no cutover/enable/promote |
| S030-D61 | Accept H2 alembic tip-drift as advisory; baseline 13 **PASS** |

## Tip CI (smoke)

https://github.com/Math-Data-Justice-Collaborative/vecinita/actions/runs/31709704821

## Next

```
Enter this into the chat to continue:
@.cursor/skills/15-service-health/SKILL.md
```
