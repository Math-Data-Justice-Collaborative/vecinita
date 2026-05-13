# 11 — Infrastructure Impact

> Auto-generated: 2026-05-12

## Render Blueprint (render.yaml)

### Current State
- Single `render.yaml` at root with 5 web services + 1 database
- Services: vecinita-agent, vecinita-frontend, vecinita-gateway, vecinita-data-management-frontend-v1, vecinita-data-management-api-v1
- Database: vecinita-postgres

### Target State
- Single `render.yaml` at root with 7 web services + 1 private service + 1 database
- Added: docs-site, pgadmin (private)
- Removed: none (all existing services carry forward with new Dockerfile paths)

### Proposed render.yaml Structure

```yaml
services:
  # === Frontend Apps ===
  - type: web
    name: vecinita-chat-frontend
    runtime: docker
    dockerfilePath: ./apps/chat-frontend/Dockerfile
    dockerContext: ./apps/chat-frontend
    healthCheckPath: /health
    plan: starter

  - type: web
    name: vecinita-data-management-frontend
    runtime: docker
    dockerfilePath: ./apps/data-management-frontend/Dockerfile
    dockerContext: ./apps/data-management-frontend
    healthCheckPath: /
    plan: starter

  - type: web
    name: vecinita-docs-site
    runtime: docker
    dockerfilePath: ./apps/docs-site/Dockerfile
    dockerContext: ./apps/docs-site
    healthCheckPath: /
    plan: starter

  # === Backend API Services ===
  - type: web
    name: vecinita-gateway
    runtime: docker
    dockerfilePath: ./apps/gateway/Dockerfile
    dockerContext: .  # Root context for packages/ access
    healthCheckPath: /health
    plan: starter

  - type: web
    name: vecinita-agent
    runtime: docker
    dockerfilePath: ./apps/agent/Dockerfile
    dockerContext: .  # Root context for packages/ access
    healthCheckPath: /health
    plan: starter

  - type: web
    name: vecinita-data-management-api
    runtime: docker
    dockerfilePath: ./apps/data-management-api/Dockerfile
    dockerContext: .  # Root context for packages/ access
    healthCheckPath: /health
    plan: starter

  # === Infrastructure Services ===
  - type: pserv  # Private service
    name: vecinita-pgadmin
    runtime: docker
    dockerfilePath: ./apps/pgadmin/Dockerfile
    dockerContext: ./apps/pgadmin
    plan: starter

databases:
  - name: vecinita-postgres
    region: virginia
    plan: basic-256mb
    databaseName: vecinita
    user: vecinita
    postgresMajorVersion: "16"
```

### Key Changes
- Dockerfile paths updated to `apps/<name>/Dockerfile`
- Backend services use root `.` as dockerContext (to access `packages/`)
- Frontend services use their own directory as dockerContext
- PgAdmin added as `pserv` (private service) type
- Docs site added as web service

## Docker Compose (Local Development)

### Current State
- 5 docker-compose files with overlapping/conflicting configs
- `docker-compose.yml` — full stack
- `docker-compose.dev.yml` — dev overrides
- `docker-compose.microservices.yml` — microservices mode
- `docker-compose.render-local.yml` — Render parity
- `docker-compose.render-parity.yml` — Render parity (another version)

### Target State
- Single `docker-compose.yml` with profiles

```yaml
# docker-compose.yml — Local Development
services:
  # === Profile: core (always needed) ===
  postgres:
    profiles: ["core", "full"]
    image: postgres:16-alpine
    # ...

  pgadmin:
    profiles: ["core", "full"]
    image: dpage/pgadmin4:latest
    # ...

  # === Profile: services (backend APIs) ===
  gateway:
    profiles: ["services", "full"]
    build:
      context: .
      dockerfile: ./apps/gateway/Dockerfile
    # ...

  agent:
    profiles: ["services", "full"]
    build:
      context: .
      dockerfile: ./apps/agent/Dockerfile
    # ...

  data-management-api:
    profiles: ["services", "full"]
    build:
      context: .
      dockerfile: ./apps/data-management-api/Dockerfile
    # ...

  # === Profile: frontends ===
  chat-frontend:
    profiles: ["frontends", "full"]
    build:
      context: ./apps/chat-frontend
    # ...

  data-management-frontend:
    profiles: ["frontends", "full"]
    build:
      context: ./apps/data-management-frontend
    # ...
```

### Usage
```bash
docker compose --profile core up          # Just postgres + pgadmin
docker compose --profile services up      # Backend services
docker compose --profile frontends up     # Frontend dev servers
docker compose --profile full up          # Everything
```

## CI/CD (GitHub Actions)

### Current State
- 17 workflow files in `.github/workflows/`
- Many are tightly coupled to the submodule structure
- No path-filtering — all workflows run on all changes

### Target State
- ~8-10 workflow files, one per app + shared quality checks
- Path-filtered: only runs when relevant files change

### Proposed Workflows

| Workflow | Trigger Paths | Actions |
|----------|--------------|---------|
| `ci-gateway.yml` | `apps/gateway/**`, `packages/**` | Lint, test, build Docker image |
| `ci-agent.yml` | `apps/agent/**`, `packages/**` | Lint, test, build Docker image |
| `ci-data-management-api.yml` | `apps/data-management-api/**`, `packages/**` | Lint, test, build |
| `ci-chat-frontend.yml` | `apps/chat-frontend/**` | Lint, test, build |
| `ci-data-management-frontend.yml` | `apps/data-management-frontend/**` | Lint, test, build |
| `ci-modal-workers.yml` | `apps/vllm-inference/**`, `apps/embedding-worker/**`, `apps/scraper-worker/**`, `apps/indexing-worker/**` | Lint, test, Modal deploy |
| `deploy-render.yml` | Push to main (after CI passes) | Render blueprint sync |
| `quality-gate.yml` | All PRs | Linting, type checking, security scan |

## .environments/ Directory

### Structure
```
.environments/
├── gateway.env                    # Gateway service env vars
├── gateway.env.example            # Documented defaults (checked in)
├── agent.env                      # Agent service env vars
├── agent.env.example
├── data-management-api.env
├── data-management-api.env.example
├── chat-frontend.env
├── chat-frontend.env.example
├── data-management-frontend.env
├── data-management-frontend.env.example
├── pgadmin.env
├── pgadmin.env.example
├── vllm-inference.env
├── vllm-inference.env.example
├── embedding-worker.env
├── embedding-worker.env.example
├── scraper-worker.env
├── scraper-worker.env.example
├── indexing-worker.env
├── indexing-worker.env.example
└── README.md                      # Documents env var ownership + descriptions
```

### .gitignore Rules
```gitignore
# Secrets — never commit
.environments/*.env
!.environments/*.env.example
```
