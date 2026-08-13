# HANDOFF — S030-corpus-automations

**Updated:** 2026-08-13  
**Session:** S030-corpus-automations (`feature`)  
**Cycle:** EV-027 · F75 F76 F77  
**Branch:** `evolve/EV-027-corpus-automations`  
**Tip:** `588dab6` (CI green)  
**Issues:** #73 · #72 · #219  

## Position

- **13-deploy-smoke** in progress — path **baseline_only_flags_off** (S030-D60)
- Tip CI PASS @ `588dab6` — [run 31709704821](https://github.com/Math-Data-Justice-Collaborative/vecinita/actions/runs/31709704821)
- Live H0c/H1/H3/H3b/H4–H5 **PASS**; H2 alembic **FAIL expected** (live `20260806_0014` vs tip `20260812_0016`)
- Report: `reports/deploy-smoke.md`
- **Await S030-D61** (H2 disposition)
- No enable / FT promote; EV-027 not on live
- PR [#238](https://github.com/Math-Data-Justice-Collaborative/vecinita/pull/238) open (no merge)

## Decisions

| ID | Choice |
|----|--------|
| S030-D58 | Resume 12; staging_as_live; push+CI; checklist-only; F75–F77 scope |
| S030-D59 | Approve mitigations 1–4 + rollback; checklist **ready** (flags off) |
| S030-D60 | Baseline live smoke only; push tip; flags off; no cutover/enable/promote |
| S030-D61 | **pending** — H2 alembic tip drift disposition |

## Tip CI

https://github.com/Math-Data-Justice-Collaborative/vecinita/actions/runs/31709704821

## Next

Await S030-D61 AskQuestion in chat (H2 disposition).
