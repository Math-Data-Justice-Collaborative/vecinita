# S005 — Routing Plan (evolve, lite)

Approved by user 2026-06-29 (AskQuestion: close S004 → open S005; Resend SMTP; full user-mgmt ops;
all email templates; remember-me toggle).

Cycle **EV-006** · Feature **F35** (admin user management + auth UX) · Extends **F34** · Issue **#75**.

| Stage | Status | Note |
|-------|--------|------|
| 00-context | completed | Session opener; research + 5 decisions (R55–R59); context-brief §16 |
| 01-requirements | completed | F35 spec; RD-080–RD-090; ADR-029; UJ-030–UJ-033; TC-088–TC-095; AC-U1–AC-U9; config/api/secrets deltas ([report](./reports/01-requirements.md)) |
| 04-tech-plan | completed | ADR-030; TP-S005-01–16; Phase 12 M48–M52; httpx Admin API; DM Modal host; audit ingest ([report](./reports/04-tech-plan.md)) |
| 07-build | pending | Users page, `/admin/users*` on DM Modal, remember-me, `supabase/templates/`, Resend SMTP config |
| 08-verify-build | pending | Milestone verify (lint/type/test/coverage) |
| 09-qa | pending | Authz tests (admin-only user mgmt); privacy (no PII in corpus DB); template contract smoke |
| 10-e2e | pending | E2E: invite flow, user list, role change, remember-me storage, template CI contract |
| 12-verify-deploy | pending | Resend SMTP secrets, Supabase config push with templates |
| 13-deploy-smoke | pending | Live invite email delivery smoke |

## Skipped stages (lite path — user-approved pattern from S004)

| Stage | Reason |
|-------|--------|
| 02-verify-plan | Lite path |
| 03-plan-tooling | Lite path |
| 05-verify-tech | Lite path |
| 06-tech-tooling | Lite path |
| 11-verify-impl | Lite path — covered by 09-qa + 10-e2e |

## Approved

User approval recorded: 2026-06-29
