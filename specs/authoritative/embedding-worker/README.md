# Embedding Worker Service Documentation
> Auto-generated: 2026-05-12

Comprehensive documentation for the Vecinita **embedding-worker** service — a serverless text embedding utility deployed on Modal GPU that converts natural-language text into dense vector representations using fastembed.

## Documents

| # | Document | Description |
|---|----------|-------------|
| 01 | [Behavior](01-behavior.md) | Core responsibilities, key behaviors, and service boundaries |
| 02 | [Data Models](02-data-models.md) | Embedding vectors, input/output schemas, and Pydantic models |
| 03 | [Integration Points](03-integration-points.md) | Gateway caller interface, PostgreSQL vector writes |
| 04 | [User Personas](04-user-personas.md) | Actors and systems that interact with the service |
| 05 | [User Journeys](05-user-journeys.md) | Step-by-step flows through the embedding pipeline |
| 06 | [Data Flow](06-data-flow.md) | Text in → vector out data pipeline |
| 07 | [Architecture](07-architecture.md) | Serverless function architecture on Modal |
| 08 | [API Contract](08-api-contract.md) | Modal function signatures and HTTP endpoint reference |
| 09 | [Dependencies](09-dependencies.md) | Runtime, dev, and infrastructure dependencies |
| 10 | [Technical Decisions](10-technical-decisions.md) | ADRs: fastembed vs sentence-transformers, model choice, invocation pattern |
| 11 | [Testing Plan](11-testing-plan.md) | Testing layers, tools, and CI integration |
| 12 | [Infrastructure Plan](12-infrastructure-plan.md) | Modal deployment, volumes, and CI/CD |
| 13 | [Modal Integration Plan](13-modal-integration-plan.md) | Detailed Modal app configuration and function specs |
| 14 | [Render Integration Plan](14-render-integration-plan.md) | N/A — runs on Modal |

## Diagrams

| Diagram | Description |
|---------|-------------|
| [Architecture](diagrams/architecture.md) | Component and deployment diagram |
| [Data Flow](diagrams/data-flow.md) | Request/response and data pipeline flows |
| [Data Models](diagrams/data-models.md) | ER diagram of embedding schemas |
| [Integration Points](diagrams/integration-points.md) | Service connectivity graph |
| [User Personas](diagrams/user-personas.md) | Actor relationship diagram |
| [User Journeys](diagrams/user-journeys.md) | Journey maps per persona |
| [Sequence Flows](diagrams/sequence-flows.md) | Key request sequence diagrams |

## Source Code

| Item | Path |
|------|------|
| Modal entrypoint | `modal-apps/embedding-modal/src/vecinita/app.py` |
| Service logic | `modal-apps/embedding-modal/src/vecinita/service.py` |
| Schemas | `modal-apps/embedding-modal/src/vecinita/schemas.py` |
| Constants | `modal-apps/embedding-modal/src/vecinita/constants.py` |
| FastAPI app factory | `modal-apps/embedding-modal/src/vecinita/api.py` |
| Dependencies | `modal-apps/embedding-modal/pyproject.toml` |
| Tests | `modal-apps/embedding-modal/tests/` |
| CI workflow | `modal-apps/embedding-modal/.github/workflows/ci.yml` |
| Deploy workflow | `modal-apps/embedding-modal/.github/workflows/deploy.yml` |
| Gateway invoker | `apis/gateway/src/services/modal/invoker.py` |
| Git submodule remote | `https://github.com/Math-Data-Justice-Collaborative/vecinita-embedding.git` |
| Target path (post-refactor) | `apps/embedding-worker/` |
