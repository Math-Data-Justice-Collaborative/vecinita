# Session brief — S000 internal docs archive

| Field | Value |
|-------|-------|
| **Session ID** | S000-internal-docs-archive |
| **Type** | `process` |
| **Status** | completed |
| **Intent** | Archive agent/ops standing docs moved off `docs/` root for wiki publish hygiene |
| **Branch** | `feat/wiki-docs-publish` |
| **Started** | 2026-07-05 |

## Scope

Relocated pre-session and internal tracker files from `docs/` root into this folder so the
published wiki and public `docs/` tree contain only long-lived product/engineering specs.

## Contents

| Path | Former location |
|------|-----------------|
| `execution-plan.md` | `docs/sessions/S000-internal-docs-archive/execution-plan.md` |
| `deploy-state.md` | `docs/sessions/S000-internal-docs-archive/deploy-state.md` |
| `deploy-report.md` | `docs/sessions/S000-internal-docs-archive/deploy-report.md` |
| `service-health-state.md` | `docs/sessions/S000-internal-docs-archive/service-health-state.md` |
| `data-staging-state.md` | `docs/sessions/S000-internal-docs-archive/data-staging-state.md` |
| `hotfix-log.md` | `docs/sessions/S000-internal-docs-archive/hotfix-log.md` |
| `project-board.md` | `docs/sessions/S000-internal-docs-archive/project-board.md` |
| `audits.md` | `docs/sessions/S000-internal-docs-archive/audits.md` |
| `context-brief.md` | `docs/sessions/S000-internal-docs-archive/context-brief.md` |
| `reference.md` | `docs/sessions/S000-internal-docs-archive/reference.md` |
| `reports/*.md` | `docs/sessions/S000-internal-docs-archive/reports/qa-report.md`, `docs/sessions/S000-internal-docs-archive/reports/e2e-report.md`, … |
| `context/*.md` | `docs/context/*.md` |

## Standing docs (remain at `docs/` root)

See [sessions/README.md](../README.md) — `spec.md`, `feature-list.md`, `test-plan.md`,
`deploy-checklist.md`, `api-contract.md`, `architecture.md`, runbooks, ADRs, etc.
