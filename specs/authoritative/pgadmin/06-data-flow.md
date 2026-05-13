# pgadmin — Data Flow

> Auto-generated: 2026-05-12

## Overview

pgAdmin's data flow is simple: all data moves between the developer's browser and the PostgreSQL database, with pgAdmin acting as a pass-through UI layer.

## Inbound Data

| Source | Format | Trigger | Destination |
|--------|--------|---------|-------------|
| Developer (browser) | HTTP form / SQL text | UI interaction / query execution | pgAdmin backend |
| PostgreSQL | PostgreSQL result sets | Query response | pgAdmin backend → browser |

## Internal Processing

| Stage | Input | Transformation | Output |
|-------|-------|----------------|--------|
| Authentication | Login credentials | Validate against internal user store | Session token |
| Query execution | Raw SQL from editor | Pass-through to PostgreSQL via libpq | Result set |
| Schema browsing | Navigation click | System catalog queries (pg_catalog) | Metadata tree |
| Data export | Result set in grid | Format conversion | CSV/JSON file |

## Outbound Data

| Destination | Format | Trigger | Content |
|-------------|--------|---------|---------|
| PostgreSQL | SQL via wire protocol | Developer executes query or browses | DDL/DML/DQL statements |
| Developer browser | HTML/JSON via HTTP | UI rendering | Query results, schema metadata |

## Data Persistence

| Store | Technology | What's Stored | Retention |
|-------|------------|---------------|-----------|
| pgAdmin internal DB | SQLite (container volume) | Server configs, saved queries, preferences | Lifetime of Docker volume |
| PostgreSQL (external) | PostgreSQL 16 | All Vecinita application data | Managed by application services |

## Diagrams

- [Data Flow Diagram](diagrams/data-flow.md)

## Related Documents

- [Data Models](02-data-models.md)
- [Integration Points](03-integration-points.md)
