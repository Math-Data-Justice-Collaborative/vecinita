# Authoritative Spec Documentation

> Auto-generated: 2026-05-12

This directory contains the authoritative documentation for the Vecinita
monorepo, produced by the spec-driven development workflow.

## Contents

### Service Documentation

| Service | Path | Description |
|---------|------|-------------|
| Agent | [agent/README.md](agent/README.md) | RAG pipeline, LLM routing, guardrails (7 docs) |
| Gateway | [gateway/README.md](gateway/README.md) | Unified HTTP entry point (14 docs + 7 diagrams) |
| Data Management API | [data-management-api/README.md](data-management-api/README.md) | Data management REST API (14 docs + 7 diagrams) |
| Embedding Worker | [embedding-worker/README.md](embedding-worker/README.md) | Batch text embedding on Modal GPU (14 docs + 7 diagrams) |
| Scraper Worker | [scraper-worker/README.md](scraper-worker/README.md) | Web scraping pipeline on Modal (14 docs + 7 diagrams) |
| Indexing Worker | [indexing-worker/README.md](indexing-worker/README.md) | Document indexing pipeline on Modal GPU — NEW (14 docs + 7 diagrams) |
| vLLM Inference | [vllm-inference/README.md](vllm-inference/README.md) | LLM inference engine on Modal GPU |

### Cross-Cutting Artifacts

| Document | Path | Description |
|----------|------|-------------|
| Dependencies | [dependencies/DEPENDENCIES.md](dependencies/DEPENDENCIES.md) | Full dependency inventory across all services |
| Environments | [environments/ENVIRONMENTS.md](environments/ENVIRONMENTS.md) | Per-service environment variable reference |
| Modal landscape | [modal/current-landscape.md](modal/current-landscape.md) | Current Modal integration state |
| Render landscape | [render/current-landscape.md](render/current-landscape.md) | Current Render integration state |
| Changelog | [changelog/CHANGELOG.md](changelog/CHANGELOG.md) | Spec-driven changelog with task completion |

## Service Documentation

| Service | Path | Description |
|---------|------|-------------|
| Gateway | [gateway/](gateway/) | Unified API gateway (14 docs) |
| Agent | [agent/](agent/) | LangGraph RAG agent (9 docs) |
| Data Management API | [data-management-api/](data-management-api/) | Data management REST API (2 docs) |
| Chat Frontend | [chat-frontend/](chat-frontend/) | End-user chat UI — React/Vite SPA (14 docs + 7 diagrams) |
| Data Management Frontend | [data-management-frontend/](data-management-frontend/) | Admin corpus management UI — React/Vite SPA (14 docs + 7 diagrams) |
| pgAdmin | [pgadmin/](pgadmin/) | PostgreSQL admin UI — Docker image (14 docs + 7 diagrams) |
| Docs Site | [docs-site/](docs-site/) | Docusaurus documentation site (14 docs + 7 diagrams) |
| vLLM Inference | [vllm-inference/](vllm-inference/) | vLLM inference service (2 docs) |

## Regeneration

To regenerate all documents, use the `create-spec` skill or run each
skill individually:

- `repo-dependencies-doc` → dependencies/
- `env-documentation` → environments/
- `modal-integration-planning` → modal/
- `render-integration-planning` → render/
- `spec-changelog` → changelog/

## Relationship to feature specs

Feature specs live under `specs/NNN-slug-name/`. The documents here are
**cross-cutting authoritative artifacts** that summarize the monorepo
state across all features. Individual feature specs reference these
when they need to understand dependencies, deployment topology, or
integration patterns.
