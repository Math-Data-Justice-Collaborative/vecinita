# Indexing Worker Service Documentation
> Auto-generated: 2026-05-12

Comprehensive documentation for the Vecinita **indexing-worker** service — a serverless document indexing pipeline deployed on Modal GPU that converts scraped documents into chunked, embedded vector representations stored in PostgreSQL (pgvector). This is a **new/planned** service; no production code exists yet.

## Documents

| # | Document | Description |
|---|----------|-------------|
| 01 | [Behavior](01-behavior.md) | Four indexing modes: single-doc, batch, selective re-index, full rebuild |
| 02 | [Data Models](02-data-models.md) | IndexingJob, DocumentChunk, VectorRecord, ContentHash schemas |
| 03 | [Integration Points](03-integration-points.md) | Gateway trigger, scraper trigger, PostgreSQL read/write |
| 04 | [User Personas](04-user-personas.md) | Automated systems, developers, platform operators |
| 05 | [User Journeys](05-user-journeys.md) | Journey maps for each indexing mode |
| 06 | [Data Flow](06-data-flow.md) | Document → chunk → embed → store pipeline |
| 07 | [Architecture](07-architecture.md) | Modal serverless with GPU, spawn_map patterns |
| 08 | [API Contract](08-api-contract.md) | Modal function signatures and invocation reference |
| 09 | [Dependencies](09-dependencies.md) | LlamaIndex, fastembed, pgvector, Modal runtime |
| 10 | [Technical Decisions](10-technical-decisions.md) | ADRs: LlamaIndex vs direct fastembed, chunking strategy, change detection |
| 11 | [Testing Plan](11-testing-plan.md) | Testing layers, mocking Modal, and CI integration |
| 12 | [Infrastructure Plan](12-infrastructure-plan.md) | Modal GPU deployment, volumes, and scaling |
| 13 | [Modal Integration Plan](13-modal-integration-plan.md) | Detailed Modal app config, GPU resources, volumes, spawn_map |
| 14 | [Render Integration Plan](14-render-integration-plan.md) | N/A — runs on Modal |

## Diagrams

| Diagram | Description |
|---------|-------------|
| [Architecture](diagrams/architecture.md) | Component and deployment diagram |
| [Data Flow](diagrams/data-flow.md) | Document → chunk → embed → store pipeline flows |
| [Data Models](diagrams/data-models.md) | ER diagram of indexing-related tables |
| [Integration Points](diagrams/integration-points.md) | Service connectivity graph |
| [User Personas](diagrams/user-personas.md) | Automated actor relationship diagram |
| [User Journeys](diagrams/user-journeys.md) | Journey maps for each indexing mode |
| [Sequence Flows](diagrams/sequence-flows.md) | Sequence diagrams for single-doc and batch indexing |

## Source Code (Planned)

| Item | Path |
|------|------|
| Modal entrypoint | `apps/indexing-worker/src/vecinita_indexing/app.py` |
| Indexing functions | `apps/indexing-worker/src/vecinita_indexing/indexer.py` |
| Chunking logic | `apps/indexing-worker/src/vecinita_indexing/chunker.py` |
| Embedding adapter | `apps/indexing-worker/src/vecinita_indexing/embedder.py` |
| Database operations | `apps/indexing-worker/src/vecinita_indexing/db.py` |
| Schemas | `apps/indexing-worker/src/vecinita_indexing/schemas.py` |
| Constants | `apps/indexing-worker/src/vecinita_indexing/constants.py` |
| Dependencies | `apps/indexing-worker/pyproject.toml` |
| Tests | `apps/indexing-worker/tests/` |

## Service Status

| Property | Value |
|----------|-------|
| Status | **Planned** — not yet implemented |
| Modal app name | `vecinita-indexing` |
| Target path | `apps/indexing-worker/` |
| Python version | >=3.11 |
| GPU required | Yes (embedding generation) |
