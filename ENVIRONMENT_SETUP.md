# Vecinita Unified Environment Configuration Guide

## Overview

Vecinita uses a **unified `.env` file** at the root of the repository that is shared by both the **Chat Application** and **Data Management System**. This ensures consistency and simplifies deployment.

## File Structure

```
/root/GitHub/VECINA/vecinita/
├── .env                                    # Unified root configuration (SHARED SOURCE OF TRUTH)
├── backend/.env                           # Backend test overrides (optional)
├── frontend/.env                          # Frontend dev server config (optional)
├── apps/data-management-frontend/.env     # Data Management specific (inherits from root)
├── services/data-management-api/apps/backend/.env  # Data Management API (inherits from root)
└── .env.example                           # Template (DO NOT EDIT)
```

## Key Supabase Configuration

All Supabase credentials are in the root `.env` file:

```bash
# Supabase URLs & Keys (SHARED BY ALL SERVICES)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=<supabase-service-role-key>                    # Service role / backend access
SUPABASE_SECRET_KEY=<supabase-service-role-key>             # Service role (backend)
SUPABASE_PUBLISHABLE_KEY=<supabase-anon-key>
SUPABASE_PERSONAL_ACCESS_TOKEN=<supabase-personal-access-token>

# Frontend-specific Supabase vars
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=<supabase-anon-key>

# Database Connection (Vector search, migrations)
DATABASE_URL=postgresql://postgres.your-project-ref:<db-password>@aws-<region>.pooler.supabase.com:5432/postgres?sslmode=require
```

## Chat Application Setup

### Start Chat Application

```bash
make dev-chat
```

This starts:
- **Frontend** (port 5173) - Chat UI
- **Gateway** (port 8004) - API gateway with Q&A endpoints
- **Agent** (port 8000) - LLM agent service

### Prerequisites

The `.env` file must include:

| Variable | Backend | Frontend | Purpose |
|----------|---------|----------|---------|
| `SUPABASE_URL` | ✅ | ✅ | Supabase project URL |
| `SUPABASE_KEY` | ✅ | ✅ | Supabase anon key |
| `SUPABASE_SECRET_KEY` | ✅ | ❌ | Service role (backend only) |
| `VITE_SUPABASE_URL` | ❌ | ✅ | Frontend Supabase URL |
| `VITE_SUPABASE_ANON_KEY` | ❌ | ✅ | Frontend anon key |
| `GROQ_API_KEY` | ✅ | ❌ | LLM provider |
| `OPENAI_API_KEY` | ✅ | ❌ | LLM provider (optional) |
| `DEEPSEEK_API_KEY` | ✅ | ❌ | LLM provider |
| `DATABASE_URL` | ✅ | ❌ | Vector search / migrations |

## Data Management System Setup

### Start Data Management System

```bash
make dev-data-management
```

This starts:
- **Data Management Frontend** (port 5174) - Data management UI
- **Data Management API** (port 8005) - Data management backend

### Prerequisites

The `.env` file must include the same **Supabase variables** as the Chat Application:
- `SUPABASE_URL`
- `SUPABASE_KEY` / `SUPABASE_SECRET_KEY`
- `VITE_SUPABASE_URL`
- `VITE_SUPABASE_ANON_KEY`
- `DATABASE_URL`

The Data Management system uses the same Supabase instance as the Chat Application.

## Individual Service Startup

### Chat Application - Components Only

```bash
# Start only the Agent (port 8000)
make dev-chat-backend

# Start only the Gateway (port 8004, uses local Agent)
make dev-gateway

# Start only the Frontend (port 5173)
make dev-chat-frontend
```

### Data Management - Components Only

```bash
# Start only Data Management API (port 8005)
make dev-data-management-api

# Start only Data Management Frontend (port 5174)
make dev-data-management-frontend
```

## Environment Variables by Component

### Chat Frontend
**Uses:**
- `VITE_SUPABASE_URL`
- `VITE_SUPABASE_ANON_KEY`
- `VITE_GATEWAY_URL` (defined in `frontend/.env`)
- `VITE_BACKEND_URL` (defined in `frontend/.env`)

**File:** `frontend/.env`

### Chat Backend (Gateway + Agent)
**Uses:**
- `SUPABASE_URL` / `SUPABASE_KEY`
- `GROQ_API_KEY`, `OPENAI_API_KEY`, `DEEPSEEK_API_KEY`
- `DEFAULT_PROVIDER`, `DEFAULT_MODEL`
- `OLLAMA_BASE_URL`
- `DATABASE_URL`
- `DEV_ADMIN_ENABLED`, `DEV_ADMIN_BEARER_TOKEN`

**Files:** `backend/.env` (optional, for overrides)

### Data Management Frontend
**Uses:**
- `VITE_SUPABASE_URL`
- `VITE_SUPABASE_ANON_KEY`

**File:** `apps/data-management-frontend/.env` (inherited from root)

### Data Management API
**Uses:**
- `SUPABASE_URL` / `SUPABASE_SECRET_KEY`
- `DATABASE_URL`
- All standard backend variables

**File:** `services/data-management-api/apps/backend/.env` (inherited from root)

## Multi-Environment Setup

### Local Development
Use the root `.env` with:
- **Supabase:** Full cloud instance (recommended)
- **Database:** Cloud Postgres via Supabase pooler
- **API Keys:** Real keys from external providers

```bash
make dev-chat
# or
make dev-data-management
```

### Staging / Production
Use deployment manifests (`render.yaml`, `render.staging.yaml`):
These pull environment variables from Render dashboard (do NOT commit to `.env`)

## Troubleshooting

### Chat Frontend Can't Connect to Backend
1. Check `VITE_GATEWAY_URL` in `frontend/.env`
2. Verify gateway is running: `make dev-chat-gateway`
3. Check Supabase credentials in root `.env`

### Data Management Frontend Can't Connect to API
1. Check data management API is running: `make dev-data-management-api`
2. Verify Supabase credentials in root `.env`
3. Check `DATABASE_URL` is correct

### Documents Tab Returns 500/503 With dpg Hostname Error
If backend logs show:

`could not translate host name "dpg-..." to address: Temporary failure in name resolution`

your local `.env` is using a Render-internal Postgres host. That hostname only resolves inside Render private networking.

Use one of these instead:
1. Local Postgres: `postgresql://postgres:postgres@localhost:5432/postgres`
2. Render external Postgres hostname from the Render dashboard (`sslmode=require`)

### Both Systems Using Different Supabase Instances
**Problem:** Chat and Data Management pointing to different Supabase projects

**Solution:**
1. Both must use variables from the same root `.env`
2. Verify all services source from root `.env`:
   ```bash
   make dev-chat     # sources root .env for Supabase
   make dev-data-management  # sources root .env for Supabase
   ```

### "Command Not Found: source"
The `.env` sourcing in Makefile requires `bash`. Ensure you're using:
```bash
make dev-chat
# NOT: sh make dev-chat
```

## Maintenance

### Adding a New Environment Variable

1. **For Chat Application only:**
   - Add to `backend/.env` with explanation
   - Or update root `.env` if shared with Data Management

2. **For Data Management only:**
   - Add to `apps/data-management-frontend/.env` or service-specific `.env`

3. **For Both Systems:**
   - Add to root `.env` with comment explaining purpose

4. **For Deployment (Render):**
   - Add to `render.yaml` / `render.staging.yaml` with `sync: false`

### Credentials Management

**DO NOT commit real credentials to `.env`:**
- Use `.env.example` for templates
- Store real `.env` locally or in password manager
- Use `git update-index --skip-worktree .env` to exclude from git tracking

## Port Mapping Summary

| Service | Port | Make Target |
|---------|------|-------------|
| Chat Frontend | 5173 | `make dev-chat-frontend` |
| Chat Agent | 8000 | `make dev-chat-backend` (via agent) |
| Chat Gateway | 8004 | `make dev-chat-backend` (via gateway) |
| Data Mgmt Frontend | 5174 | `make dev-data-management-frontend` |
| Data Mgmt API | 8005 | `make dev-data-management-api` |
| PostgreSQL | 5432 | docker-compose |
| ChromaDB | 8002 | docker-compose |

## See Also

- [SERVICE_CONNECTIVITY.md](docs/deployment/SERVICE_CONNECTIVITY.md) - Service routing and Supabase integration
- [Render Deployment Guide](docs/deployment/MULTI_REPO_CICD_ORCHESTRATION.md)
