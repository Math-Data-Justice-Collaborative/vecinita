# Vecinita pipeline skills

Skills for building **Vecinita** — a RAG service with database-backed data management
(ingest, chunk, embed, query, admin).

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

## Templates

- [template-registry.md](template-registry.md) — `api` / `worker` / `monolith`
- [deployment-catalog.md](deployment-catalog.md) — Postgres, pgvector, deploy targets

## Legacy note

These skills were adapted from an RFantibody/Modal GPU pipeline. Stages **00–17** and
orchestration patterns are unchanged; domain content targets RAG + data management.
