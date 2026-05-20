# Vecinita pipeline skills

Skills for building **Vecinita** — a RAG service with database-backed data management
(ingest, chunk, embed, query, admin).

## Pipeline state (all skills)

**Single file:** repo-root [`workflow-state.yaml`](../../workflow-state.yaml)

**Schema and update rules:** [workflow-state-reference.md](workflow-state-reference.md)

Every stage skill reads and updates the same YAML on invocation and after each substep.
Detail trackers (`docs/execution-plan.md`, `docs/deploy-state.md`, etc.) supplement but do not
replace `workflow-state.yaml`.

## Quick routing

| Goal | Skill |
|------|--------|
| Full greenfield build | [pipeline](pipeline/SKILL.md) |
| Requirements interview | [01-requirements](01-requirements/SKILL.md) |
| Technical plan | [04-tech-plan](04-tech-plan/SKILL.md) |
| Implement tasks | [07-build](07-build/SKILL.md) |
| Corpus + DB setup | [data-management](data-management/SKILL.md) |
| Production health | [15-service-health](15-service-health/SKILL.md) |
| Bug fix after deploy | [14-hotfix](14-hotfix/SKILL.md) |
| CORS / UI wiring gates (all stages) | [connectivity-gates](connectivity-gates.md) |

## Templates

- [template-registry.md](template-registry.md) — `api` / `worker` / `monolith`
- [deployment-catalog.md](deployment-catalog.md) — Postgres, pgvector, deploy targets
- [connectivity-gates.md](connectivity-gates.md) — CORS + `VITE_*` gates (H4–H5) before UI deploy sign-off

## Legacy note

These skills were adapted from an RFantibody/Modal GPU pipeline. Stages **00–17** and
orchestration patterns are unchanged; domain content targets RAG + data management.
