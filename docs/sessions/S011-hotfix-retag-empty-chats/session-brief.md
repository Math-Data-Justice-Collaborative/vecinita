# S011 — Hotfix retag 500 + empty previous chats

**Type:** hotfix  
**Branch:** `fix/BUG-2026-07-25-retag-llm-500`  
**Orchestrator:** 14-hotfix → 15-service-health  

## Intent

1. Fix GitHub [#146](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/146) —
   Manage Tags LLM retag returns `{"detail":"Internal Server Error"}`.
2. Then fix GitHub [#145](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/145) —
   previous chats restore with empty Vecinita assistant content.
3. After merge: staging smoke (user choice B).

## Session decisions

| ID | Choice |
|----|--------|
| S011-D1 | #146 then #145 |
| S011-D2 | Close S010, open hotfix session |
| S011-D3 | Fix + staging smoke after merge |

## Prior session

S010-unify-llm-service closed/parked (EV-011 T80.7 still blocked).

## Bug reports

- `docs/bug-reports/BUG-2026-07-25-retag-llm-internal-server-error.md` (#146)
- `docs/bug-reports/BUG-2026-07-25-previous-chats-empty-assistant.md` (#145) — queued
