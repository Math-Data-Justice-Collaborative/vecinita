# User Personas: Embedding Worker
> Auto-generated: 2026-05-12

## Overview

The embedding worker is a backend utility with no direct human users. All interactions are programmatic — initiated by the gateway service, CI/CD pipelines, or developers during local testing.

## Personas

### P1: Gateway Service (Automated System)

| Attribute | Value |
|-----------|-------|
| Type | Automated system |
| Role | Primary consumer of embedding functions |
| Interaction | `modal.Function.from_name().remote()` |
| Frequency | 50-500 invocations/day |
| Needs | Low-latency vector generation, consistent dimensions, reliable availability |

The gateway calls `embed_query` and `embed_batch` to generate vectors for user questions during the RAG pipeline. It requires deterministic 384-dimensional output and sub-2s warm response times.

### P2: Developer (Human)

| Attribute | Value |
|-----------|-------|
| Type | Human |
| Role | Builds, tests, and deploys the embedding service |
| Interaction | `modal deploy`, `modal run`, local FastAPI via `uvicorn`, pytest |
| Frequency | During development cycles |
| Needs | Fast local iteration, clear test output, straightforward deployment |

Developers use the FastAPI HTTP interface (`POST /embed`, `POST /embed/batch`) for local testing and the Modal CLI for deployment. They run `make test` and `make lint` for quality checks.

### P3: CI/CD Pipeline (Automated System)

| Attribute | Value |
|-----------|-------|
| Type | Automated system |
| Role | Runs lint, tests, and deploys on push to `main` |
| Interaction | GitHub Actions workflows |
| Frequency | On every push/PR |
| Needs | Deterministic test results, fast feedback, credential-gated deploy |

The CI pipeline (`modal-apps/embedding-modal/.github/workflows/ci.yml`) runs `make lint` then `make test`. The deploy pipeline (`deploy.yml`) additionally runs `modal deploy main.py` with `MODAL_TOKEN_ID` and `MODAL_TOKEN_SECRET` from GitHub Secrets.

### P4: Modal Platform (Infrastructure)

| Attribute | Value |
|-----------|-------|
| Type | Infrastructure platform |
| Role | Hosts and scales the serverless functions |
| Interaction | Container lifecycle, Volume management, function scheduling |
| Frequency | Every invocation |
| Needs | Valid app definition, image spec, Volume mount, timeout config |

Modal manages container cold starts, model Volume persistence, and function timeout enforcement. It provides the execution environment (debian_slim + Python 3.11 + fastembed).

## Persona-to-Function Map

| Persona | `embed_query` | `embed_batch` | HTTP API | `modal deploy` | pytest |
|---------|:---:|:---:|:---:|:---:|:---:|
| Gateway Service | Yes | Yes | — | — | — |
| Developer | Yes (via `modal run`) | Yes (via `modal run`) | Yes | Yes | Yes |
| CI/CD Pipeline | — | — | — | Yes | Yes |
| Modal Platform | Yes (hosts) | Yes (hosts) | — | Yes (receives) | — |

See: [User Journeys](05-user-journeys.md) | [Architecture](07-architecture.md)
