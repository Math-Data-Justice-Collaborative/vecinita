# pgadmin — High-Level Behavior

> Auto-generated: 2026-05-12

## Purpose

pgadmin is a private, internal-only PostgreSQL management UI deployed as the official `dpage/pgadmin4` Docker image. It provides a web-based interface for the solo developer to inspect, query, and manage the Vecinita PostgreSQL database across all schemas. It is not publicly accessible and serves purely as a developer tool.

## Responsibilities

| Responsibility | Description |
|----------------|-------------|
| Database browsing | Browse tables, views, functions, and schemas across the Vecinita database |
| Query execution | Run ad-hoc SQL queries against any schema |
| Schema inspection | View table definitions, indexes, constraints, and relationships |
| Data editing | View and edit row data directly in the UI |
| Server management | Manage PostgreSQL server connections and credentials |
| Backup/restore | Trigger database backups and restores via the pgAdmin UI |

## Key Behaviors

### Database Connection

- **Trigger:** Developer navigates to the pgAdmin web UI
- **Process:** pgAdmin authenticates the developer with configured default credentials, then presents the server tree with pre-configured PostgreSQL connections
- **Outcome:** Developer has full admin access to all Vecinita database schemas

### Ad-hoc Query Execution

- **Trigger:** Developer opens the Query Tool for a specific database
- **Process:** pgAdmin provides a SQL editor with syntax highlighting, auto-complete, and execution against the connected PostgreSQL instance
- **Outcome:** Query results displayed in a tabular format with export options

### Schema Exploration

- **Trigger:** Developer expands the server tree to inspect tables, columns, indexes
- **Process:** pgAdmin reads PostgreSQL system catalogs and presents metadata in a navigable tree
- **Outcome:** Full visibility into database structure without needing CLI tools

## Boundaries

- Does NOT manage application-level migrations (handled by Alembic in backend services)
- Does NOT provide API access to other services (internal tool only)
- Does NOT handle data transformations or ETL (handled by scraper/data-management-api)
- Does NOT enforce application-level access controls (raw database admin)
- Does NOT run in production/staging environments on Render — local and private only

## Related Documents

- [Architecture](07-architecture.md)
- [Integration Points](03-integration-points.md)
- [Architecture Diagram](diagrams/architecture.md)
