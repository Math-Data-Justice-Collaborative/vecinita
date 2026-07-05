# Feature inspection — URL & route reference

## Environment URLs

### Local (`docs/LOCAL_DEV.md`)

| Service | Base URL | Swagger |
|---------|----------|---------|
| ChatRAG frontend | `http://localhost:5173` | — |
| Admin frontend | `http://localhost:5174` | — |
| ChatRAG backend | `http://localhost:8000` | `/docs` |
| Internal write API | `http://localhost:8002` | `/docs` |
| Data Management API | Modal `serve` URL (printed in terminal) | `/docs` |

### Staging (`docs/deploy-state.md`)

| Service | Env var | Typical URL pattern |
|---------|---------|---------------------|
| ChatRAG frontend | `VECINITA_STAGING_CHAT_FRONTEND_URL` | `https://vecinita-chat-rag-frontend-*.ondigitalocean.app` |
| Admin frontend | `VECINITA_STAGING_ADMIN_FRONTEND_URL` | `https://vecinita-admin-frontend-*.ondigitalocean.app` |
| ChatRAG backend | `VECINITA_STAGING_CHAT_URL` | `https://vecinita-chat-rag-backend-*.ondigitalocean.app` |
| Internal write API | `VECINITA_STAGING_WRITE_URL` | `https://vecinita-internal-write-api-*.ondigitalocean.app` |
| Data Management API | `VECINITA_STAGING_ADMIN_API_URL` | `https://vecinita--vecinita-data-management-*.modal.run` |

Prefer `workflow-state.yaml` §`deployment.staging.urls` when populated; fall back to deploy-state.

## OpenAPI ↔ backend map

| OpenAPI file | Backend app | Local module |
|--------------|-------------|--------------|
| `openapi/chat-rag.yaml` | ChatRAG backend (DO) | `vecinita_chat_rag_backend` |
| `openapi/internal-write.yaml` | Internal write API (DO) | `vecinita_internal_write_api` |
| `openapi/data-management.yaml` | Data Management (Modal ASGI) | `vecinita_data_management_backend` |

On conflict, **OpenAPI in repo wins** (ADR-011); Swagger UI reflects the running app's generated schema — flag drift if they differ.

## Admin frontend routes

From `apps/data-management-frontend/src/App.tsx`:

| Route | Page | Typical features |
|-------|------|------------------|
| `/login` | Login | F34 auth |
| `/dashboard` | Dashboard | F25 summary |
| `/corpus` | Corpus | F9, F20–F21, F27 |
| `/jobs` | Jobs | F32, F37 eval rows |
| `/health` | Health | F26 |
| `/audit` | Audit | F29 |
| `/users` | Users | F35 |
| `/evaluation` | Evaluation | F36, F37 — use `?tab=` (`dashboard`, `explore`, `criteria`, `playground`) |
| `/forgot-password`, `/reset-password`, `/accept-invite` | Auth flows | F35 |

## ChatRAG frontend paths

Path-based (not React Router file routes):

| Path | View |
|------|------|
| `/` | Chat panel |
| `/corpus` | Corpus browse |

## Mapping UJ → inspection targets

Use `docs/user-journeys.md` **Entry point** column:

| Entry pattern | UI base | API Swagger |
|---------------|---------|-------------|
| ChatRAG Frontend → | Chat FE URL + `/` or `/corpus` | Chat backend `/docs` |
| Admin UI → `/…` | Admin FE URL + path | Write `/docs` and/or DM `/docs` |
| Modal `POST /jobs` | Admin `/jobs` | DM `/docs` → `/jobs` |
| `POST /api/v1/ask` | Chat `/` | Chat `/docs` → `/api/v1/ask` |
| `/internal/v1/…` | Admin page calling API | Write `/docs` |

## Starting local servers (reminder)

```bash
# Postgres + migrations — see docs/LOCAL_DEV.md
uv run uvicorn vecinita_internal_write_api.app:create_app --factory --host 0.0.0.0 --port 8002
uv run uvicorn vecinita_chat_rag_backend.app:create_app --factory --host 0.0.0.0 --port 8000
cd apps/chat-rag-frontend && npm run dev      # :5173
cd apps/data-management-frontend && npm run dev  # :5174
# DM API: modal serve (infra/modal/README.md)
```
