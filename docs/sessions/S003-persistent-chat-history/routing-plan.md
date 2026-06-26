# S003 — Routing Plan (evolve-lite)

Approved by user 2026-06-26 (AskQuestion: routing=approve, scope=both, privacy=sessionStorage).

| Stage | Status | Note |
|---|---|---|
| 00-context | in_progress | This session opener; feature delta — browser-local persistent chat history |
| 01-requirements | pending | Delta — add Fn for persistent chat history + previous-chats list; UJ for revisit/persist; ADR-004 revisit |
| 04-tech-plan | pending | Delta — sessionStorage persistence layer for `useChatHistory`; previous-conversations model + UI |
| 07-build | pending | TDD: persistence hook + previous-chats list UI + i18n |
| 09-qa | pending | Full-repo QA (lint/typecheck/tests) |
| 10-e2e | pending | New UJ: refresh/tab-away persistence + revisit a previous chat |
| 12-verify-deploy | pending | Pre-deploy gate |
| 13-deploy-smoke | pending | Deploy + H1–H5 smokes |

## Skipped stages

| Stage | Reason |
|---|---|
| 02-verify-plan | Evolve-lite — small, well-understood frontend delta |
| 03-plan-tooling | No new tooling/guardrails needed |
| 05-verify-tech | Evolve-lite — small tech delta |
| 06-tech-tooling | No new tooling/guardrails needed |
| 11-verify-impl | Evolve-lite — covered by 09-qa + 10-e2e |
