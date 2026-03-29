# Vecinita Environment & Startup Setup - Summary

## What Was Done

### 1. ✅ Created Separate Make Commands

#### For Chat Application
```bash
make dev-chat              # Start frontend + gateway + agent
make dev-chat-frontend     # Frontend only (port 5173)
make dev-chat-backend      # Agent + Gateway (ports 8000, 8004)
```

#### For Data Management System
```bash
make dev-data-management        # Start frontend + API
make dev-data-management-frontend # Frontend only (port 5174)
make dev-data-management-api     # API only (port 8005)
```

#### Legacy Individual Targets
```bash
make dev-frontend   # Chat frontend (legacy)
make dev-backend    # Chat agent (legacy)
make dev-gateway    # Chat gateway (legacy)
```

### 2. ✅ Unified `.env` File Configuration

**Single source of truth:** Root `.env` file is sourced by both Chat and Data Management systems

**All Supabase credentials preserved:**
- ✅ SUPABASE_URL
- ✅ SUPABASE_KEY  
- ✅ SUPABASE_SECRET_KEY
- ✅ SUPABASE_PUBLISHABLE_KEY
- ✅ DATABASE_URL
- ✅ All API keys (GROQ, OpenAI, DeepSeek, Tavily, etc.)
- ✅ All LangSmith configuration
- ✅ All Modal credentials
- ✅ All deployment hooks

**Frontend-specific variables:**
- ✅ VITE_SUPABASE_URL
- ✅ VITE_SUPABASE_ANON_KEY

### 3. ✅ Supabase Properly Wired

Both systems now explicitly source from root `.env`:

```makefile
# Chat Gateway - Makefile
dev-chat-gateway:
  cd backend && source ../.env && \
    uv run -m uvicorn src.api.main:app ...

# Data Management API - Makefile
dev-data-management-api:
  cd services/data-management-api/apps/backend && source ../../../.env && \
    npm run dev
```

This ensures both see the **same Supabase instance** and can share data.

### 4. ✅ Documentation Created

Three comprehensive guides added to repository:

| Document | Purpose |
|----------|---------|
| `DEV_STARTUP.md` | Quick start guide for developers |
| `ENVIRONMENT_SETUP.md` | Complete environment configuration reference |
| `SUPABASE_CONFIGURATION.md` | Detailed Supabase wiring and integration |

## File Changes Summary

### Modified Files
- **Makefile** - Added new targets for dev-chat and dev-data-management
- **`.env`** - Added clarifying comments about component usage (secrets preserved)
- **`.env.example`** - No changes (template file remains)

### New Files
- **DEV_STARTUP.md** - Developer quick-start guide
- **ENVIRONMENT_SETUP.md** - Complete environment setup documentation
- **SUPABASE_CONFIGURATION.md** - Supabase integration guide

### Files NOT Changed (Secrets Preserved)
✅ All API keys intact
✅ All database credentials intact
✅ All Supabase keys intact
✅ All deployment hooks intact

## How to Use

### Start Chat Application
```bash
# Ensure .env file exists with Supabase credentials
make dev-chat

# Or start components individually
make dev-chat-backend &
make dev-chat-frontend
```

### Start Data Management System
```bash
# Uses same .env as Chat Application
make dev-data-management

# Or start components individually
make dev-data-management-api &
make dev-data-management-frontend
```

### Run Both Simultaneously
```bash
# Terminal 1
make dev-chat

# Terminal 2
make dev-data-management

# Both share the same Supabase instance and can access each other's data
```

## Supabase Connectivity

### Chat Frontend
- **Port:** 5173
- **Supabase Keys:** `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY` 
- **Auth:** JWT tokens via Supabase Auth
- **Sourced from:** Root `.env` → `frontend/.env` → Environment

### Chat Backend (Agent + Gateway)
- **Agent Port:** 8000
- **Gateway Port:** 8004
- **Supabase Keys:** `SUPABASE_URL`, `SUPABASE_KEY`, `DATABASE_URL`
- **Features:** Auth token validation, vector search, document queries
- **Sourced from:** Root `.env` (via `source ../.env` in Makefile)

### Data Management Frontend
- **Port:** 5174
- **Supabase Keys:** Same as Chat Frontend (`VITE_*` vars)
- **Auth:** Shares Supabase instance with Chat Frontend
- **Sourced from:** Root `.env` → `apps/data-management-frontend/.env`

### Data Management API
- **Port:** 8005
- **Supabase Keys:** Same as Chat Backend (`SUPABASE_*` vars)
- **Features:** Document management, data operations
- **Sourced from:** Root `.env` (via `source ../../../.env` in Makefile)

## Environment Variable Sourcing

```
Root .env (SOURCE OF TRUTH)
    ├─→ Chat Frontend (.env source: root .env)
    ├─→ Chat Backend (Makefile sources: ../.env)
    ├─→ Chat Gateway (Makefile sources: ../.env)
    ├─→ DM Frontend (.env source: root .env)
    └─→ DM API (Makefile sources: ../../../.env)

RESULT: All services see same Supabase instance
```

## Troubleshooting

### Both systems must use same Supabase instance
**How to verify:**
```bash
# Terminal 1: Chat Backend
make dev-chat-backend  # Check logs for "SUPABASE_URL="

# Terminal 2: Data Management API
make dev-data-management-api  # Check logs must show SAME URL as Terminal 1
```

### If services can't find Supabase
1. Check `.env` exists: `ls -la .env`
2. Check format: `grep SUPABASE_URL .env`
3. Verify Makefile sourcing works: `source .env && echo $SUPABASE_URL`
4. Restart services after .env changes

### Frontend can't reach backend
1. Chat Frontend talks to Gateway on port 8004
2. Check Gateway is running: `make dev-chat-gateway`
3. Verify: `curl http://localhost:8004/health`

## Key Points Preserved

✅ **NO secrets were removed**
✅ **NO breaking changes** - all old make targets still work
✅ **Unified configuration** - single .env file for both systems
✅ **Proper Supabase wiring** - both systems use same cloud instance
✅ **Clear documentation** - three new guides for developers

## Next Steps

1. **Read** `DEV_STARTUP.md` for quick start
2. **Review** `ENVIRONMENT_SETUP.md` for detailed configuration
3. **Understand** `SUPABASE_CONFIGURATION.md` for cloud integration
4. **Run** `make dev-chat` or `make dev-data-management`
5. **Share** `.env.example` template with team (never share real `.env`)

## Questions?

- **How do both systems use same database?** → They source from root `.env` which has same `SUPABASE_URL`
- **Can I run them at the same time?** → Yes! They use different ports and share Supabase
- **Why unified .env?** → Ensures consistency, prevents misconfigurations, simplifies deployment
- **What if I need service-specific config?** → Backend/.env and frontend/.env can override (not needed for Supabase)
