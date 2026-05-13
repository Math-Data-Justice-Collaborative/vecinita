# Scraper Worker Service Documentation
> Auto-generated: 2026-05-12

Comprehensive documentation for the Vecinita **scraper-worker** service — the queue-based web scraping and content extraction pipeline running on Modal serverless.

## Documents

| # | Document | Description |
|---|----------|-------------|
| 01 | [Behavior](01-behavior.md) | Core responsibilities, key behaviors, and service boundaries |
| 02 | [Data Models](02-data-models.md) | Scraping jobs, crawled URLs, document chunks, embeddings |
| 03 | [Integration Points](03-integration-points.md) | Gateway calls, PostgreSQL writes, embedding service, Playwright/Crawl4AI |
| 04 | [User Personas](04-user-personas.md) | Actors and roles that interact with the scraper |
| 05 | [User Journeys](05-user-journeys.md) | Scrape job lifecycle, reindex flow |
| 06 | [Data Flow](06-data-flow.md) | 5-stage pipeline: scrape → process → chunk → embed → store |
| 07 | [Architecture](07-architecture.md) | Queue-based pipeline architecture on Modal |
| 08 | [API Contract](08-api-contract.md) | Modal functions + FastAPI REST endpoints |
| 09 | [Dependencies](09-dependencies.md) | Runtime, dev, and infrastructure dependencies |
| 10 | [Technical Decisions](10-technical-decisions.md) | ADRs (decided) and pending decisions |
| 11 | [Testing Plan](11-testing-plan.md) | Testing layers, tools, and CI integration |
| 12 | [Infrastructure Plan](12-infrastructure-plan.md) | Modal serverless + Render DM API facade |
| 13 | [Modal Integration Plan](13-modal-integration-plan.md) | Queues, secrets, spawn patterns, resources |
| 14 | [Render Integration Plan](14-render-integration-plan.md) | Render DM API deployment details |

## Diagrams

| Diagram | Description |
|---------|-------------|
| [Architecture](diagrams/architecture.md) | Component and deployment diagram |
| [Data Flow](diagrams/data-flow.md) | 5-stage pipeline flow |
| [Data Models](diagrams/data-models.md) | ER diagram of scraper-owned tables |
| [Integration Points](diagrams/integration-points.md) | Service connectivity graph |
| [User Personas](diagrams/user-personas.md) | Actor relationship diagram |
| [User Journeys](diagrams/user-journeys.md) | Journey maps per persona |
| [Sequence Flows](diagrams/sequence-flows.md) | Key request sequence diagrams |

## Source Code

| Item | Path |
|------|------|
| Modal app entry | `modal-apps/scraper/src/vecinita_scraper/app.py` |
| Workers module | `modal-apps/scraper/src/vecinita_scraper/workers/` |
| FastAPI REST API | `modal-apps/scraper/src/vecinita_scraper/api/` |
| Configuration | `modal-apps/scraper/src/vecinita_scraper/config.py` |
| Dockerfile | `modal-apps/scraper/Dockerfile` |
| Git submodule | `modal-apps/scraper` → `vecinita-scraper.git` |
| Target path | `apps/scraper-worker/` (post-refactor) |
