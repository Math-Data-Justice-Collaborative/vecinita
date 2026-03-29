# Vecinita Development Startup Guide

## Quick Start

### Start the Chat Application
```bash
make dev-chat
```
Starts: Frontend (5173) + Gateway (8004) + Agent (8000)

### Start the Data Management System
```bash
make dev-data-management
```
Starts: Frontend (5174) + API (8005)

### Start Individual Components
```bash
make dev-chat-frontend        # Chat UI only (port 5173)
make dev-chat-backend         # Chat Agent + Gateway (ports 8000, 8004)
make dev-chat-gateway         # Chat Gateway only (port 8004)

make dev-data-management-frontend  # Data Mgmt UI only (port 5174)
make dev-data-management-api       # Data Mgmt API only (port 8005)
```

## Prerequisites

### 1. Environment Configuration
Ensure `.env` file exists in the repository root with:

**Required Supabase Configuration** (same for both Chat and Data Management):
```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=<supabase-service-role-key>
SUPABASE_SECRET_KEY=<supabase-service-role-key>
SUPABASE_PUBLISHABLE_KEY=<supabase-anon-key>

VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=<supabase-anon-key>

DATABASE_URL=postgresql://postgres.your-project-ref:<db-password>@aws-<region>.pooler.supabase.com:5432/postgres?sslmode=require
```

**Required for Chat Backend Only**:
```bash
GROQ_API_KEY=gsk_...
OPENAI_API_KEY=sk-proj-...
DEEPSEEK_API_KEY=sk-...
```

### 2. Install Dependencies
```bash
# Backend
cd backend
uv sync

# Frontend (Chat)
cd frontend
npm ci

# Data Management Frontend (if running)
cd apps/data-management-frontend
npm ci

# Data Management API (if running)
cd services/data-management-api/apps/backend
uv sync
```

### 3. Start Docker Services (Optional but Recommended)
```bash
# Start PostgreSQL, ChromaDB, and other services
docker-compose up -d
```

## Service Connectivity

### Chat Application
**Frontend** ← calls → **Gateway** ← calls → **Agent**
- Frontend on port 5173
- Gateway on port 8004 (uses Supabase)
- Agent on port 8000 (uses Supabase for vector search)

### Data Management System
**DM Frontend** ← calls → **DM API**
- Frontend on port 5174
- API on port 8005 (uses same Supabase as Chat)

## Supabase Integration

### Chat Frontend
- Uses `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY` for authentication
- Configured in `frontend/.env` (sourced from root `.env`)

### Chat Backend (Gateway + Agent)
- Uses `SUPABASE_URL` and `SUPABASE_KEY` for queries
- Uses `DATABASE_URL` for vector embeddings and migrations
- Both sourced from root `.env`

### Data Management System
- Frontend uses same Supabase as Chat Frontend
- API uses same Supabase as Chat Backend
- All sourced from root `.env`

## Troubleshooting

### "Supabase connection refused"
1. Check `.env` has valid `SUPABASE_URL` and credentials
2. Verify you're connected to internet (Supabase is cloud-hosted)
3. Test connection: `curl "$SUPABASE_URL"`

### "Cannot reach Gateway from Frontend"
1. Verify Gateway is running: `ps aux | grep port 8004`
2. Check `frontend/.env` has correct `VITE_GATEWAY_URL`
3. Test Gateway health: `curl http://localhost:8004/health`

### "Cannot reach Data Management API"
1. Verify API is running: Check port 8005
2. Ensure `.env` is sourced correctly in Data Management API
3. Check database connectivity: `echo $DATABASE_URL`

### "Different systems see different database"
- Both Chat and Data Management MUST source from root `.env`
- Check: `source .env && echo $SUPABASE_URL`
- Both should output the same URL

## Environment Variables Reference

| Variable | Used By | Purpose | Example |
|----------|---------|---------|---------|
| `SUPABASE_URL` | Chat Backend, DM API | Cloud database URL | `https://...supabase.co` |
| `SUPABASE_KEY` | Both frontends | Anonymous key | `sb_public_...` |
| `SUPABASE_SECRET_KEY` | Both backends | Service role key | `<supabase-service-role-key>` |
| `VITE_SUPABASE_URL` | Chat Frontend, DM Frontend | Frontend Supabase URL | `https://...supabase.co` |
| `VITE_SUPABASE_ANON_KEY` | Chat Frontend, DM Frontend | Frontend anon key | `sb_public_...` |
| `DATABASE_URL` | Chat Backend, DM API | Connection pooling URL | `postgresql://...` |
| `GROQ_API_KEY` | Chat Backend | LLM provider | `gsk_...` |
| `DEEPSEEK_API_KEY` | Chat Backend | LLM provider | `sk-...` |

## Port Allocation

```
CHAT APPLICATION:
  5173 - Frontend (Vue)
  8000 - Agent (Python FastAPI)
  8004 - Gateway (Python FastAPI)

DATA MANAGEMENT:
  5174 - Frontend (Vue/React)
  8005 - API (Python/Node)

LOCAL SERVICES:
  5432 - PostgreSQL
  8002 - ChromaDB
  3001 - PostgREST (optional)
```

## Running Both Systems Simultaneously

You can run Chat and Data Management at the same time since they use different ports:

```bash
# Terminal 1: Chat Application
make dev-chat

# Terminal 2: Data Management System  
make dev-data-management

# Or in one terminal with background jobs:
make dev-chat &
make dev-data-management &
```

Both will share the same Supabase instance (from root `.env`), so they can see each other's data.

## Key Files

- **Root Environment:** `/root/GitHub/VECINA/vecinita/.env` - SHARED by all services
- **Build Instructions:** `/root/GitHub/VECINA/vecinita/ENVIRONMENT_SETUP.md`
- **Makefile:** `/root/GitHub/VECINA/vecinita/Makefile` - Define all make targets
- **Chat Frontend Env:** `/root/GitHub/VECINA/vecinita/frontend/.env`
- **Chat Backend Env:** `/root/GitHub/VECINA/vecinita/backend/.env` (optional)

## See Also

- `ENVIRONMENT_SETUP.md` - Complete environment configuration guide
- `docs/deployment/SERVICE_CONNECTIVITY.md` - Service routing and architecture
- `.env.example` - Environment template (reference, do not edit)
