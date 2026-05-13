# pgadmin — Dependencies

> Auto-generated: 2026-05-12

## Overview

pgAdmin is an off-the-shelf Docker image with minimal dependencies. It requires only Docker and a PostgreSQL instance to connect to.

## Internal Dependencies (monorepo)

| Package/Module | Path | Purpose |
|----------------|------|---------|
| docker-compose.yml | `docker-compose.yml` | Service definition and networking |

No monorepo code dependencies — pgAdmin is a pre-built image.

## External Dependencies (runtime)

| Package | Version | Purpose | Critical |
|---------|---------|---------|----------|
| dpage/pgadmin4 | latest | PostgreSQL admin web UI | Yes |

All runtime dependencies are bundled inside the Docker image.

## Infrastructure Dependencies

| Resource | Provider | Purpose |
|----------|----------|---------|
| PostgreSQL | Docker Compose (local) | Database to administer |
| Docker | Local machine | Container runtime |

## Service Dependencies (runtime calls)

| Service | Required | Fallback |
|---------|----------|----------|
| PostgreSQL (vecinita-postgres) | Yes | pgAdmin starts but cannot connect to any database |

## Related Documents

- [Infrastructure Plan](12-infrastructure-plan.md)
- [Integration Points](03-integration-points.md)
