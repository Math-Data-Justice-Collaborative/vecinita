# Environment Files

Per-service environment variable configuration for Vecinita.

## Structure

Each service has two files:

- `<service>.env` — actual environment values (gitignored, never commit)
- `<service>.env.example` — documented defaults and placeholders (tracked in git)

## Usage

```bash
# Copy example to create your local env file
cp .environments/gateway.env.example .environments/gateway.env
# Edit with your actual values
```

## Services

| File | Service | Deploy Target |
|------|---------|---------------|
| `gateway.env` | API Gateway | Render |
| `agent.env` | RAG Agent | Render |
| `data-management-api.env` | Data Management API | Render |
| `chat-frontend.env` | Chat Frontend | Render |
| `data-management-frontend.env` | DM Frontend | Render |
| `pgadmin.env` | PgAdmin | Render (private) |
| `vllm-inference.env` | vLLM Inference | Modal |
| `embedding-worker.env` | Embedding Worker | Modal |
| `scraper-worker.env` | Scraper Worker | Modal |
| `indexing-worker.env` | Indexing Worker | Modal |
| `docs-site.env` | Documentation Site | Render/GH Pages |

## Full Reference

See `specs/authoritative/environments/ENVIRONMENTS.md` for the complete
environment variable catalog with cross-service matrix and deployment targets.
