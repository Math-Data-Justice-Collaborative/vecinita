# pgadmin — Architecture

> Auto-generated: 2026-05-12

## Overview

pgAdmin 4 is an off-the-shelf PostgreSQL administration tool. The Vecinita project uses the official `dpage/pgadmin4` Docker image with no custom code. Architecture is entirely determined by the upstream pgAdmin project.

## Architecture Style

Pre-built containerized web application (off-the-shelf). No custom application code.

## Component Map

| Component | Responsibility | Source Path |
|-----------|---------------|-------------|
| pgAdmin 4 Web UI | Browser-based PostgreSQL admin interface | `dpage/pgadmin4` Docker image (upstream) |
| pgAdmin Backend (Python/Flask) | API layer, query execution, server management | Bundled in Docker image |
| Internal SQLite | Persists server configs, saved queries, user prefs | Container volume at `/var/lib/pgadmin` |
| Docker Compose Service | Container orchestration and networking | `docker-compose.yml` (pgadmin service) |

## Runtime Characteristics

| Property | Value |
|----------|-------|
| Language / runtime | Python 3.x (Flask) — bundled in Docker image |
| Framework | pgAdmin 4 (Flask-based) |
| Entry point | Docker image entrypoint (upstream) |
| Port | 5050 (mapped from container port 80) |
| Health check | HTTP GET on port 80 (container internal) |

## Concurrency Model

Handled entirely by the upstream pgAdmin image. Uses Gunicorn with multiple workers behind the Flask application. Single-user usage pattern (solo developer) means concurrency is not a concern.

## Diagrams

- [Architecture Diagram](diagrams/architecture.md)

## Related Documents

- [Behavior](01-behavior.md)
- [Infrastructure Plan](12-infrastructure-plan.md)
