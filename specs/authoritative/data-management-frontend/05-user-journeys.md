# data-management-frontend — User Journeys

> Auto-generated: 2026-05-12

## Overview

All journeys involve an authenticated admin managing the RAG corpus and scraping pipeline.

## Journeys

### Submit a Scraping Job

**Persona:** Admin / Developer
**Goal:** Scrape a website and add its content to the RAG corpus

| Step | Action | System Response | Notes |
|------|--------|-----------------|-------|
| 1 | Navigate to Add Document (`/add`) | Scrape form displayed | |
| 2 | Enter target URL and configure depth | Form validates URL format | |
| 3 | Configure chunking options (optional) | Chunk size, overlap sliders | |
| 4 | Enable auto-tagging (optional) | Toggle switch | |
| 5 | Click "Start Scraping" | `POST /jobs` sent to DM API | Job remembered in localStorage |
| 6 | Redirect to Scrape Jobs page | Job appears with "queued" status | |
| 7 | Monitor progress | Status polls: pending → crawling → chunking → embedding → completed | Progress bar updates |

**Happy path outcome:** Website scraped, chunked, embedded, and added to corpus.
**Failure modes:** DM API cold start (warmup banner), crawl timeout, embedding service unavailable, URL unreachable.

### Browse and Edit Corpus

**Persona:** Admin / Developer
**Goal:** Review and manage documents in the corpus

| Step | Action | System Response | Notes |
|------|--------|-----------------|-------|
| 1 | Navigate to Corpus View (`/corpus`) | Paginated document list displayed | |
| 2 | Search or filter by type/language/tags | Filtered results shown | |
| 3 | Click a document | Document detail page (`/document/:id`) | |
| 4 | Edit metadata or tags | Update form | |
| 5 | Save changes | `PUT /documents/:id` | Toast confirmation |
| 6 | Delete document (if needed) | `DELETE /documents/:id` with confirmation dialog | |

**Happy path outcome:** Document metadata updated or removed from corpus.
**Failure modes:** API timeout, concurrent edit conflicts.

### Review Dashboard Statistics

**Persona:** Admin / Developer
**Goal:** Get an overview of corpus health

| Step | Action | System Response | Notes |
|------|--------|-----------------|-------|
| 1 | Open Dashboard (`/`) | Stats cards and charts load | |
| 2 | View total documents, embeddings | Stats cards displayed | |
| 3 | Review by-type and by-language breakdowns | Bar/pie charts rendered | |
| 4 | Check recent documents | Recent document list | |

**Happy path outcome:** Clear picture of corpus size, composition, and recent additions.
**Failure modes:** Backend warming up (fallback stats shown with banner), both document and job endpoints fail (local mock data displayed).

## Diagrams

- [User Journey Diagram](diagrams/user-journeys.md)

## Related Documents

- [User Personas](04-user-personas.md)
- [Behavior](01-behavior.md)
