# pgadmin — User Journeys

> Auto-generated: 2026-05-12

## Overview

All journeys involve the solo developer using pgAdmin as a database administration tool during local development or debugging.

## Journeys

### Inspect Database State After Migration

**Persona:** Solo Developer
**Goal:** Verify that an Alembic migration applied correctly

| Step | Action | System Response | Notes |
|------|--------|-----------------|-------|
| 1 | Open pgAdmin at `localhost:5050` | Login page displayed | Default credentials from docker-compose |
| 2 | Log in with default email/password | Server tree displayed | |
| 3 | Expand Vecinita server → database → Schemas → public → Tables | Table list shown | |
| 4 | Right-click target table → Properties | Column definitions, constraints, indexes displayed | |
| 5 | Verify new columns/constraints match migration | Visual confirmation | |

**Happy path outcome:** Developer confirms migration applied correctly.
**Failure modes:** pgAdmin cannot connect (Postgres not running), table not found (migration failed silently).

### Run Diagnostic Query

**Persona:** Solo Developer
**Goal:** Debug a data issue by running ad-hoc SQL

| Step | Action | System Response | Notes |
|------|--------|-----------------|-------|
| 1 | Navigate to server → database in tree | Database selected | |
| 2 | Open Query Tool (Tools → Query Tool) | SQL editor opens | |
| 3 | Write and execute diagnostic SQL query | Results displayed in grid | Supports EXPLAIN ANALYZE |
| 4 | Export results if needed | CSV/JSON download | |

**Happy path outcome:** Developer identifies the data issue.
**Failure modes:** Query timeout (long-running query), permission denied (should not occur with superuser).

### Browse Embeddings/Vector Data

**Persona:** Solo Developer
**Goal:** Verify vector embeddings stored by the scraper/embedding pipeline

| Step | Action | System Response | Notes |
|------|--------|-----------------|-------|
| 1 | Navigate to embeddings table | Table view displayed | |
| 2 | View rows with vector columns | Truncated vector display | pgvector columns shown as arrays |
| 3 | Run similarity query in Query Tool | Matching rows returned | Uses pgvector `<=>` operator |

**Happy path outcome:** Developer verifies embeddings are stored correctly.
**Failure modes:** pgvector extension not installed, vector columns display poorly in grid view.

## Diagrams

- [User Journey Diagram](diagrams/user-journeys.md)

## Related Documents

- [User Personas](04-user-personas.md)
- [Behavior](01-behavior.md)
