# S012 — Hotfix admin UI (#112 + #105)

**Type:** hotfix  
**Status:** in_progress  
**Branch:** `fix/S012-admin-ui-112-105`  
**Orchestrator:** 14-hotfix → 15-service-health  

## Intent

1. Fix GitHub [#112](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/112) —
   Admin Corpus Documents table lacks pagination (server-side, mirror Users / public browse).
2. Fix GitHub [#105](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/105) —
   Spanish “Sign out all devices” overflows the desktop sidebar footer.
3. One branch / one PR; merge + deploy only after explicit approval; then staging smoke
   via 15-service-health.

## Session decisions

| ID | Choice |
|----|--------|
| S012-D1 | Both issues in **one** branch/PR |
| S012-D2 | Open hotfix session S012 |
| S012-D3 | Symptoms seen on **staging** |
| S012-D4 | #112 as **hotfix** (API pagination + FE) |
| S012-D5 | Merge + deploy after explicit approval |

## Bug reports

- `docs/bug-reports/BUG-2026-07-28-admin-corpus-pagination.md` (#112)
- `docs/bug-reports/BUG-2026-07-28-spanish-signout-overflow.md` (#105)
