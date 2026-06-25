# Vecinita pipeline skills

Skills for building **Vecinita** — a RAG service with database-backed data management
(ingest, chunk, embed, query, admin).

## Pipeline state (all skills)

**Single file:** repo-root [`workflow-state.yaml`](../../workflow-state.yaml)

**Sole writer:** [workflow-state-manager](../agents/workflow-state-manager.md) — pipeline
skills invoke the agent for `read_context` and `update`; they do not edit the YAML directly.

**Schema and protocol:** [workflow-state-reference.md](workflow-state-reference.md),
[workflow-state-agent-protocol.md](workflow-state-agent-protocol.md)

Detail trackers (`docs/execution-plan.md`, `docs/deploy-state.md`, etc.) supplement but do not
replace workflow-state.

## Sessions (session-first work model)

Every bounded unit of work runs inside a **session** (`S{NNN}-slug`) opened by
[00-context](00-context/SKILL.md) with a user-approved routing plan. Session reports live under
`docs/sessions/{id}/reports/`; standing specs stay in `docs/` root.

**Convention:** [sessions-reference.md](sessions-reference.md) ·
**Index:** [`docs/sessions/README.md`](../../docs/sessions/README.md)

## Quick routing

| Goal | Skill |
|------|--------|
| Open a work session | [00-context](00-context/SKILL.md) |
| Full greenfield build | [00-context](00-context/SKILL.md) → [pipeline](pipeline/SKILL.md) |
| **Add feature(s) to existing app** | [00-context](00-context/SKILL.md) → [16-evolve](16-evolve/SKILL.md) |
| Requirements interview | [01-requirements](01-requirements/SKILL.md) |
| Technical plan | [04-tech-plan](04-tech-plan/SKILL.md) |
| Implement tasks | [07-build](07-build/SKILL.md) |
| Corpus + DB setup | [data-management](data-management/SKILL.md) |
| Production health | [15-service-health](15-service-health/SKILL.md) |
| Bug fix after deploy | [14-hotfix](14-hotfix/SKILL.md) |
| GitHub Projects board setup | [github-projects](github-projects/SKILL.md) |
| CORS / UI wiring gates (all stages) | [connectivity-gates](connectivity-gates.md) |

**Any stage 00–17** can accept "add features X, Y, Z" during an active `feature`/`new_service`
session with an evolve cycle (delta mode). Without a session,
[workflow-state-manager](../agents/workflow-state-manager.md) routes to **00-context** → **16-evolve**.

## Shared preamble

All numbered skills (00–17) follow [pipeline-preamble.md](pipeline-preamble.md) and the
session-first model in [sessions-reference.md](sessions-reference.md).

## Templates

- [template-registry.md](template-registry.md) — `api` / `worker` / `monolith`
- [deployment-catalog.md](deployment-catalog.md) — Postgres, pgvector, deploy targets
- [connectivity-gates.md](connectivity-gates.md) — CORS + `VITE_*` gates (H4–H5) before UI deploy sign-off

## Legacy note

These skills were adapted from an RFantibody/Modal GPU pipeline. Stages **00–17** and
orchestration patterns are unchanged; domain content targets RAG + data management.
