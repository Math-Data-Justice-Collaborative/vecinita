# S011 — Hotfix retag 500 + empty previous chats

**Type:** hotfix  
**Status:** completed (2026-07-26)  
**Branch:** `fix/BUG-2026-07-25-retag-llm-500` → merged `main` @ `f61f820` (PR #147)  
**Orchestrator:** 14-hotfix → 15-service-health  

## Intent

1. Fix GitHub [#146](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/146) —
   Manage Tags LLM retag returns `{"detail":"Internal Server Error"}`.
2. Then fix GitHub [#145](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/145) —
   previous chats restore with empty Vecinita assistant content.
3. After merge: staging smoke (user choice B).

## Outcome

Both bugs resolved and closed. Staging confirmed working by user (S011-D6).  
Report: `reports/service-health.md`.

## Session decisions

| ID | Choice |
|----|--------|
| S011-D1 | #146 then #145 |
| S011-D2 | Close S010, open hotfix session |
| S011-D3 | Fix + staging smoke after merge |
| S011-D4 | PROXY_KEY sync — Ask/stream unblocked |
| S011-D5 | Proceed commit → PR → merge |
| S011-D6 | User confirmed live working; close session |

## Prior session

S010-unify-llm-service closed/parked (EV-011 T80.7 still blocked).

## Bug reports

- `docs/bug-reports/BUG-2026-07-25-retag-llm-internal-server-error.md` (#146) — resolved
- `docs/bug-reports/BUG-2026-07-25-previous-chats-empty-assistant.md` (#145) — resolved
