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
| S000 | process | completed | Internal docs archive (moved off `docs/` root for wiki hygiene) | `feat/wiki-docs-publish` | 2026-07-05 | 2026-07-05 |
| S001 | ops | in_progress | Modal LLM cold-start reduction via GPU memory snapshots | `feat/S001-modal-cold-start-snapshot` | 2026-06-25 | — |
| S002 | feature | paused | Admin job management + ingest tag resilience (#88/#89) | `feat/S002-admin-job-management` | 2026-06-26 | — |
| S003 | feature | completed | Browser-local persistent chat history (F33) | `feat/S003-persistent-chat-history` | 2026-06-26 | 2026-06-28 (QA/e2e/deploy deferred) |
| S004 | feature | completed | Supabase Auth for admin surfaces (#75) — invite-only, admin+viewer; merged PR #100; deploy-verify deferred | `feat/S004-supabase-auth` | 2026-06-28 | 2026-06-29 (deploy 12/13 deferred) |
| S005 | feature | paused | Admin user mgmt + remember-me + Resend SMTP + email templates (EV-006 / F35); deploy 12/13 deferred | `feat/S005-user-mgmt-auth` | 2026-06-29 | — |
| S006 | feature | paused | Complete invite acceptance flow — #109 (EV-007 / F35 gap); parked for S007 | `feat/S006-invite-acceptance` | 2026-06-30 | — |
| S007 | feature | in_progress | Admin RAG evaluation tab + golden set — #99 (EV-008 / F36) | `feat/S007-rag-eval` | 2026-07-01 | — |
| S012 | hotfix | completed | Admin UI #112 pagination + #105 ES sidebar | `fix/S012-hotfix-admin-ui-112-105` | 2026-07-28 | 2026-07-28 |
| S013 | feature | completed | Unified job monitoring (#116) | `evolve/EV-012-unified-job-monitoring` | 2026-07-29 | 2026-07-29 |
| S014 | feature | completed | Admin Corpus & dashboard UI/UX polish (#148) | `main` (merged #154) | 2026-07-29 | 2026-07-29 |
| S019 | feature | completed | Batch A retrieval quality (F42 H7+P1) | `evolve/EV-016-retrieval-quality` (merged #172) | 2026-07-31 | 2026-08-01 |
| S020 | feature | completed | Retrieval Batch B (F43 cache + #83/#161 + #162) | `evolve/EV-017-retrieval-batch-b` (merged #173) | 2026-08-02 | 2026-08-02 |
| S021 | feature | completed | Empty retrieve + CE re-gate follow-on (#83 / AC-BB9); RET-001 via #177 | `evolve/EV-018-retrieval-follow-on` (merged #174); RET #177 @ 6e3207d | 2026-08-02 | 2026-08-02 |
| S022 | feature | completed | Ingest resilience (#163/#166/#160 → F47–F49) | `evolve/EV-019-ingest-resilience` | 2026-08-02 | 2026-08-02 |
| S023 | feature | completed | Residual top_k=8 + default P3 packing (F50/F51) | `evolve/EV-020-retrieval-topk-packing` | 2026-08-02 | 2026-08-03 |
| S024 | feature | completed | Website scrape & crawl pipeline (epic #185 → #69/#71/#70) | `evolve/EV-022-website-scrape-crawl` | 2026-08-03 | 2026-08-03 |
| S025 | feature | completed | CI / local quality + release automation (#194 → #182/#103; F62/F63) | `evolve/EV-023-ci-release-automation` | 2026-08-03 | 2026-08-04 |
| S026 | feature | in_progress | ChatRAG + Admin UX polish epic (#193 → #87/#93/#104/#106/#186/#170) | `evolve/EV-024-frontend-ux-polish` | 2026-08-04 | — |

## Active session

**S026-frontend-ux-polish** / **EV-024** — epic [#193](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/193). Branch `evolve/EV-024-frontend-ux-polish`. Predecessor S025/EV-023 closed 2026-08-04.

## Folder layout

```
docs/sessions/SNNN-slug/
  session-brief.md      # intent, type, scope, links to standing docs
  routing-plan.md       # approved stage list + skip rationale
  roadmap.md            # GitHub issue decomposition + dependency diagrams (after 04-tech-plan)
  reports/              # qa-report, e2e-report, verification-report, etc.
  checkpoints/          # optional phase gate digests
```

## Standing docs vs session reports

| Kind | Location |
|------|----------|
| Long-lived specs | `docs/spec.md`, `feature-list.md`, `test-plan.md`, `deploy-checklist.md`, … |
| Session outputs | `docs/sessions/{id}/reports/*.md` |
| Scoped discovery | `docs/sessions/S000-internal-docs-archive/context/{slug}.md` (new work: link from session brief) |
| Agent/ops archive | `docs/sessions/S000-internal-docs-archive/` |

Pre-session reports archived under `docs/sessions/S000-internal-docs-archive/reports/` are **historical read-only**.
New QA, verification, E2E, and verify-impl reports **must** use `docs/sessions/{id}/reports/`.
See `.cursor/rules/session-reports.mdc`.
