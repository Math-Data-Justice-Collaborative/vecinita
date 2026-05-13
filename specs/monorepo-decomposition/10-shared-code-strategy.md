# 10 — Shared Code Strategy

> Auto-generated: 2026-05-12

## Current Shared Code

| Location | Contents | Used By |
|----------|----------|---------|
| `packages/openapi-clients/` | Generated TypeScript + Python API clients | Frontends, gateway |
| `packages/python/db` | Database utilities | Gateway, agent |
| `clients/apis/` | API client wrappers | Gateway |

## Target Strategy

### Principle: Extract the minimum shared surface

For a solo developer, minimize shared packages. Only extract code that:
1. Is used by 2+ services AND
2. Would be painful to duplicate AND
3. Changes infrequently (stable interface)

### packages/db

**Purpose**: Database models, migrations, connection utilities shared across
all Python backend services.

**Contents**:
- SQLAlchemy/ORM model definitions (one file per schema)
- Migration scripts (Alembic or equivalent)
- Connection pool factory
- Schema constants (schema names, table names)

**Consumers**: gateway, agent, data-management-api

**Important**: Each service only imports models for its own schema. The `db`
package provides all models but services should only use their own schema's
models at runtime.

```python
# In apps/gateway/src/main.py
from packages.db.models.gateway import ScrapingJob, JobStatus

# In apps/agent/src/main.py
from packages.db.models.agent import Conversation, VectorEmbedding
```

### packages/config

**Purpose**: Shared configuration loading, environment variable parsing,
validation.

**Contents**:
- Env var loader that reads from `.environments/<service>.env`
- Config validation (required vars, type coercion)
- Environment detection (local, staging, production)

**Consumers**: All Python services

### packages/common

**Purpose**: Shared types, constants, error classes used across services.

**Contents**:
- Error classes (ServiceError, ValidationError, NotFoundError)
- Shared constants (API versions, status codes, schema names)
- Shared type definitions (Pydantic models for inter-service communication)

**Consumers**: gateway, agent, data-management-api

### What Gets Removed

| Current | Action | Reason |
|---------|--------|--------|
| `packages/openapi-clients/` | Remove | TD-006: Drop generated clients |
| `clients/apis/` | Remove | Replaced by simple HTTP calls |

### Python Package Installation

Each shared package uses `pyproject.toml` with a local path dependency:

```toml
# apps/gateway/pyproject.toml
[project]
dependencies = [
    "packages-db @ file://../../packages/db",
    "packages-config @ file://../../packages/config",
    "packages-common @ file://../../packages/common",
]
```

In Docker, packages are copied and installed via pip:

```dockerfile
# apps/gateway/Dockerfile
COPY packages/ /app/packages/
COPY apps/gateway/ /app/apps/gateway/
RUN pip install /app/packages/db /app/packages/config /app/packages/common
RUN pip install /app/apps/gateway/
```
