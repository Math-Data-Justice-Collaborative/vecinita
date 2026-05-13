# pgadmin — Data Models

> Auto-generated: 2026-05-12

## Overview

pgadmin does not own any data domain. It is a read/write admin tool that operates on the Vecinita PostgreSQL database, which is owned by backend services (gateway, agent, data-management-api). pgAdmin's own internal state (saved queries, server bookmarks, user preferences) is stored in its internal SQLite database within the container volume.

## Models

### pgAdmin Internal State (container-managed)

pgAdmin manages its own internal data in a SQLite database. This is not part of the Vecinita data model.

| Data | Storage | Persistence | Description |
|------|---------|-------------|-------------|
| Server connections | SQLite (internal) | Container volume | Saved PostgreSQL server connection definitions |
| Saved queries | SQLite (internal) | Container volume | Developer's saved SQL queries |
| User preferences | SQLite (internal) | Container volume | UI preferences, layout settings |
| Query history | SQLite (internal) | Container volume | History of executed queries |

## Relationships

pgAdmin reads and writes all tables owned by other services:

| Service Owner | Schemas/Tables Accessed | Access Level |
|---------------|------------------------|--------------|
| Gateway | Public schema (conversations, messages, scraping_jobs, etc.) | Read/Write (admin) |
| Agent | Public schema (agent-related tables) | Read/Write (admin) |
| Data Management API | Public schema (documents, corpus, embeddings, etc.) | Read/Write (admin) |

## Diagrams

- [ER Diagram](diagrams/data-models.md)

## Related Documents

- [API Contract](08-api-contract.md)
- [Data Flow](06-data-flow.md)
