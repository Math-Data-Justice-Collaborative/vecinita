# HANDOFF — S030-corpus-automations

**Updated:** 2026-08-13  
**Session:** S030-corpus-automations (`feature`)  
**Cycle:** EV-027 · F75 F76 F77  
**Branch:** `evolve/EV-027-corpus-automations`  
**Tip:** `e9e2629` (CI green)  
**Issues:** #73 · #72 · #219  

## Position

- Phase D verify complete (09–11)
- **12-verify-deploy** COMPLETE **ready** — `reports/deploy-checklist.md`
- **env_role:** `staging_as_live` = **live/prod** (sole stack; separate staging later)
- **Next:** **13-deploy-smoke** (flags off; AskQuestion before enable/promote)
- PR [#238](https://github.com/Math-Data-Justice-Collaborative/vecinita/pull/238) open (no merge)

## Decisions (12)

| ID | Choice |
|----|--------|
| S030-D58 | Resume 12; staging_as_live; push+CI; checklist-only; F75–F77 scope |
| S030-D59 | Approve mitigations 1–4 + rollback; checklist **ready** (flags off) |

## Tip CI

https://github.com/Math-Data-Justice-Collaborative/vecinita/actions/runs/31707365293

## Next

```
Enter this into the chat to continue:
@.cursor/skills/13-deploy-smoke/SKILL.md
```
