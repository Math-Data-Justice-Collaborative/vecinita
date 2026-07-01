# Sessions index

Session-specific artifacts for bounded work units. Standing project docs remain in `docs/` root.

**Convention:** [sessions-reference.md](../../.cursor/skills/sessions-reference.md)

## Quick start

```
@00-context I want to <your goal>
```

00-context will:

1. Classify session type (`greenfield`, `feature`, `hotfix`, `integration`, `new_service`, `ops`, `process`)
2. Allocate the next id (`S001`, `S002`, …)
3. Create this folder with `session-brief.md` and `routing-plan.md`
4. Ask you to approve the routing plan
5. Set `active_session` in `workflow-state.yaml`

Then invoke stages from the approved plan (e.g. `@10-e2e`, `@16-evolve`).

## Index

| Session ID | Type | Status | Intent | Branch | Started | Completed |
|------------|------|--------|--------|--------|---------|-----------|
| S001 | ops | in_progress | Modal LLM cold-start reduction via GPU memory snapshots | `feat/S001-modal-cold-start-snapshot` | 2026-06-25 | — |
| S002 | feature | paused | Admin job management + ingest tag resilience (#88/#89) | `feat/S002-admin-job-management` | 2026-06-26 | — |
| S003 | feature | completed | Browser-local persistent chat history (F33) | `feat/S003-persistent-chat-history` | 2026-06-26 | 2026-06-28 (QA/e2e/deploy deferred) |
| S004 | feature | completed | Supabase Auth for admin surfaces (#75) — invite-only, admin+viewer; merged PR #100; deploy-verify deferred | `feat/S004-supabase-auth` | 2026-06-28 | 2026-06-29 (deploy 12/13 deferred) |
| S005 | feature | paused | Admin user mgmt + remember-me + Resend SMTP + email templates (EV-006 / F35); deploy 12/13 deferred | `feat/S005-user-mgmt-auth` | 2026-06-29 | — |
| S006 | feature | paused | Complete invite acceptance flow — #109 (EV-007 / F35 gap); parked for S007 | `feat/S006-invite-acceptance` | 2026-06-30 | — |
| S007 | feature | in_progress | Admin RAG evaluation tab + golden set — #99 (EV-008 / F36) | `feat/S007-rag-eval` | 2026-07-01 | — |

## Active session

**S007-rag-eval** — see `docs/sessions/S007-rag-eval/` and
`workflow-state.yaml` §`active_session`.

## Folder layout

```
docs/sessions/SNNN-slug/
  session-brief.md      # intent, type, scope, links to standing docs
  routing-plan.md       # approved stage list + skip rationale
  reports/              # qa-report, e2e-report, verification-report, etc.
  checkpoints/          # optional phase gate digests
```

## Standing docs vs session reports

| Kind | Location |
|------|----------|
| Long-lived specs | `docs/spec.md`, `feature-list.md`, `test-plan.md`, `deploy-checklist.md`, … |
| Session outputs | `docs/sessions/{id}/reports/*.md` |
| Scoped discovery | `docs/context/{slug}.md` |

Pre-session reports at `docs/` root (e.g. `docs/qa-report.md`) are **historical read-only**.
New QA, verification, E2E, and verify-impl reports **must** use `docs/sessions/{id}/reports/`.
See `.cursor/rules/session-reports.mdc`.
