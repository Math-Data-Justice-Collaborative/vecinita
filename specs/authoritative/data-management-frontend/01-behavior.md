# data-management-frontend — High-Level Behavior

> Auto-generated: 2026-05-12

## Purpose

The data-management frontend is an admin UI for managing the Vecinita RAG corpus. Admins and developers use it to add, edit, and delete documents, submit web scraping jobs, manage tags, view corpus statistics, and configure scraper settings. It communicates with the data-management API for document/corpus CRUD and the gateway for job triggering.

## Responsibilities

| Responsibility | Description |
|----------------|-------------|
| Document CRUD | List, view, create, update, and delete documents in the corpus |
| Scrape job management | Submit new scraping jobs, monitor progress, cancel running jobs |
| Tag management | View tag inventory, auto-generate tags, apply tags to documents |
| Corpus statistics | Display dashboard with document counts, embedding counts, type/language breakdowns |
| Document upload | Upload PDF, DOCX, and other files for processing and embedding |
| Semantic search | Search the vector database for similar documents |
| Embedding generation | Trigger embedding generation for individual documents |
| Admin authentication | API-key-based authentication for protected routes |
| i18n support | English/Spanish locale switching via `LocaleContext` |

## Key Behaviors

### Submit Scraping Job

- **Trigger:** Admin enters a URL, configures depth/options, and clicks "Scrape"
- **Process:** `ragApi.scrapeUrl()` sends a `POST /jobs` to the DM API with crawl config, chunking config, and metadata. Job ID remembered in localStorage for status tracking.
- **Outcome:** Job appears in the Scrape Jobs view with real-time status polling

### Manage Documents

- **Trigger:** Admin navigates to the documents dashboard or corpus view
- **Process:** `ragApi.getDocuments()` fetches paginated documents from `GET /documents`. Admin can search, filter by type/language/tags, view details, edit metadata, or delete.
- **Outcome:** Full CRUD lifecycle for corpus documents

### Monitor Scrape Job Status

- **Trigger:** Admin views the Scrape Jobs page
- **Process:** `ragApi.getScrapeJobs()` fetches job list from `GET /jobs`, hydrates known local jobs, maps Modal statuses to frontend statuses, infers progress percentages.
- **Outcome:** Real-time job progress with stage indicators (pending → crawling → extracting → chunking → embedding → completed)

### Tag Inventory Management

- **Trigger:** Admin navigates to Tags view
- **Process:** `ragApi.getAllTags()` fetches tag inventory from `GET /tags` with optional locale parameter. Tags displayed with resource counts.
- **Outcome:** Full tag inventory with counts, filterable by locale

## Boundaries

- Does NOT run scraping or embedding workloads (delegated to DM API and Modal workers)
- Does NOT directly access the database (all operations through the DM API)
- Does NOT handle chat Q&A (handled by chat-frontend)
- Does NOT manage LLM providers or models (handled by agent/gateway)

## Related Documents

- [Architecture](07-architecture.md)
- [Integration Points](03-integration-points.md)
- [Architecture Diagram](diagrams/architecture.md)
