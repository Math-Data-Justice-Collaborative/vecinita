# data-management-frontend — User Personas

> Auto-generated: 2026-05-12

## Overview

The data-management frontend serves admins and developers who manage the RAG corpus and scraping pipeline.

## Personas

### Admin / Developer

| Attribute | Value |
|-----------|-------|
| Role | Platform administrator — manages corpus, configures scraping, reviews data quality |
| Interaction mode | Web UI (browser) — authenticated |
| Goals | Add documents to corpus, submit scraping jobs, manage tags, monitor embedding pipeline, review corpus stats |
| Pain points | Cold start delays on DM API, complex scraper configuration, need visibility into job progress |

## Actor-System Map

| Persona | Touchpoint | Access Level |
|---------|------------|--------------|
| Admin / Developer | Dashboard (`/`) | Read (authenticated) |
| Admin / Developer | Corpus View (`/corpus`) | Read/Write (authenticated) |
| Admin / Developer | Add Document (`/add`) | Write (authenticated) |
| Admin / Developer | Document Detail (`/document/:id`) | Read/Write (authenticated) |
| Admin / Developer | Scrape Jobs (`/scrape-jobs`) | Read/Write (authenticated) |
| Admin / Developer | Tags View (`/tags`) | Read (authenticated) |
| Admin / Developer | Settings (`/settings`) | Read/Write (authenticated) |
| Admin / Developer | Admin Access (`/admin-access`) | Admin (authenticated) |
| Admin / Developer | Login (`/login`) | Auth flow |

## Diagrams

- [User Personas Diagram](diagrams/user-personas.md)

## Related Documents

- [User Journeys](05-user-journeys.md)
- [Behavior](01-behavior.md)
