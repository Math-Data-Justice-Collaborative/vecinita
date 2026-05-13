# pgadmin — Integration Points

> Auto-generated: 2026-05-12

## Overview

pgadmin has a single integration point: the Vecinita PostgreSQL database. It does not integrate with any other Vecinita services, external APIs, or message queues.

## Internal Integrations

| Target | Protocol | Direction | Purpose | Config |
|--------|----------|-----------|---------|--------|
| PostgreSQL (vecinita-postgres) | PostgreSQL wire protocol (port 5432) | Outbound | Full admin access to all schemas | `PGADMIN_SERVER_JSON_FILE` or manual server config |

## External Integrations

None. pgadmin is a self-contained admin tool with no external API calls.

## Integration Details

### PostgreSQL Connection

- **Endpoint/Function:** PostgreSQL server at `postgres:5432` (Docker network) or `localhost:5432` (host)
- **Request format:** PostgreSQL wire protocol (libpq)
- **Response format:** PostgreSQL result sets
- **Error handling:** pgAdmin displays connection errors in the UI with diagnostic details
- **Retry/timeout policy:** Manual reconnect via UI; no automatic retry
- **Authentication:** PostgreSQL username/password (`postgres` / configured password)
- **Connection pooling:** pgAdmin manages its own connection pool per server registration

## Diagrams

- [Integration Diagram](diagrams/integration-points.md)
- [Sequence Flows](diagrams/sequence-flows.md)

## Related Documents

- [Architecture](07-architecture.md)
- [Dependencies](09-dependencies.md)
