# ✅ Local Testing Setup - Complete Implementation

## 🎉 Summary

Successfully set up a complete local test environment using Docker that isolates testing from production Supabase. All services are running and verified.

**Date Completed:** February 8, 2026  
**Status:** ✅ **READY FOR TESTING**

---

## 📊 Environment Status

### Local Test Services (Docker)
| Service | Status | Address |
|---------|--------|---------|
| PostgreSQL (pgvector) | ✅ Running | `localhost:54321` |
| PostgREST API | ✅ Running | `http://localhost:3001` |
| pgAdmin | ✅ Running | `http://localhost:5051` |

**Test Credentials:**
```
PostgreSQL:
  - Host: localhost
  - Port: 54321
  - User: postgres
  - Password: postgres
  - Database: postgres

pgAdmin:
  - URL: http://localhost:5051
  - Email: test@example.com
  - Password: test123
```

### Backend API (Local)
| Service | Status | Address |
|---------|--------|---------|
| Vecinita Backend | ✅ Running | `http://localhost:8001` |

**Test Endpoints:**
- Health: `http://localhost:8001/health` ✅
- Root: `http://localhost:8001/` ✅
- Q&A: `http://localhost:8001/ask?question=<query>&lang=en`

### Production Supabase (Cloud)
| Component | Status |
|-----------|--------|
| Credentials | 🔐 Secured in root `.env` |
| Access | ❌ Not initialized (schema missing) |
| Isolation | ✅ Separate from testing |

---

## 📁 Created Files & Modifications

### NEW: `/supabase/` Directory

```
supabase/
├── docker-compose.yml          # Test container orchestration
├── init-local-db.sql           # Database schema (from backend/scripts/)
├── init-local-db.sh            # Schema initialization script ✅
├── start-local.sh              # Main startup script ✅
├── test-connection.sh          # Verification script ✅
├── config.toml                 # Supabase CLI config
├── .env.test                   # Test env template (safe to commit)
└── README.md                   # Documentation

Key Image Change:
  - FROM: postgres:16-alpine (missing pgvector)
  - TO:   pgvector/pgvector:pg16 ✅ (includes vector support)
```

### UPDATED: `backend/.env`

**Changed from production to local test:**
```diff
- SUPABASE_URL=https://dosbzlhijkeircyainwz.supabase.co
+ SUPABASE_URL=http://localhost:3001

- SUPABASE_KEY=<production_key>
+ SUPABASE_KEY=test-anon-key-local-development-only

- DATABASE_URL=postgresql://postgres:pass@db.dosbzlhijkeircyainwz.supabase.co:5432/postgres
+ DATABASE_URL=postgresql://postgres:postgres@localhost:54321/postgres

- DB_HOST=db.dosbzlhijkeircyainwz.supabase.co
+ DB_HOST=localhost

- DB_PORT=5432
+ DB_PORT=54321
```

**API Keys Retained:**
- ✅ DEEPSEEK_API_KEY (for testing with real LLM)
- ✅ GROQ_API_KEY
- ✅ OPEN_API_KEY
- ✅ TAVILY_API_KEY
- ✅ All other credentials

### CREATED: `SECURITY_ENV_GUIDE.md`

Comprehensive guide for managing production vs test environments with security best practices.

### UPDATED: `.gitignore`

Added patterns to protect secrets:
```
# Supabase local volumes  
supabase/.env
supabase/volumes/
supabase/postgres_test_data/

# General secrets
*.pem
*.key
*.key.json
credentials.json
secrets.yaml
```

---

## ✅ Verification Checklist

### Docker Services
- ✅ PostgreSQL with pgvector extension running
- ✅ PostgREST API responding at port 3001
- ✅ pgAdmin accessible at port 5051
- ✅ All containers healthy after restart

### Database Schema
- ✅ Vector extension installed
- ✅ document_chunks table created
- ✅ search_similar_documents RPC function created
- ✅ All indexes created
- ✅ Sample data inserted (1 row)
- ✅ PostgREST schema cache reloaded

### Backend Integration
- ✅ Backend connects to local PostgREST
- ✅ Supabase client initializes successfully
- ✅ Health endpoint responds: `/health` → `{"status": "ok"}`
- ✅ API root endpoint operational
- ✅ LLM providers configured (DeepSeek primary, Groq fallback)

### Security
- ✅ Production credentials in gitignored root `.env`
- ✅ Test credentials use dummy values (safe to commit)
- ✅ Separate Supabase instances (production vs test)
- ✅ Separate database ports (5432 vs 54321)
- ✅ Separate PostgREST ports (production vs 3001)

---

## 🚀 Quick Start Commands

### Start Test Environment
```bash
cd supabase
./start-local.sh
# Containers will start and schema will auto-initialize
```

### Verify Setup
```bash
cd supabase
./test-connection.sh
# Should show all ✅ checkmarks
```

### Test Backend Connection
```bash
# Backend is already configured for local Supabase
curl http://localhost:8001/health
# Response: {"status": "ok"}
```

### Stop Test Environment
```bash
cd supabase
docker-compose down
```

### Access Database Directly
```bash
# Via psql
psql -h localhost -p 54321 -U postgres -d postgres

# Via pgAdmin
http://localhost:5051
# Email: test@example.com
# Password: test123

# Via PostgREST API
curl http://localhost:3001/document_chunks?limit=1
```

---

## 🔄 Switching Between Environments

### Switch to LOCAL Testing
```bash
# Already configured in backend/.env
cd backend
uv run uvicorn src.agent.main:app --reload
# Uses: http://localhost:3001 (PostgREST)
```

### Switch to PRODUCTION (if needed)
```bash
# Update backend/.env with root .env values:
# SUPABASE_URL=https://dosbzlhijkeircyainwz.supabase.co
# DATABASE_URL=postgresql://...@db.dosbzlhijkeircyainwz.supabase.co:5432/postgres

cd backend
uv run uvicorn src.agent.main:app --reload
# Uses: https://dosbzlhijkeircyainwz.supabase.co (Cloud)
```

---

## 📋 Next Steps

### For Testing
1. Local test environment is ready
2. Backend is configured to use local Supabase
3. Run tests with: `uv run pytest`
4. Test the Q&A functionality with sample documents

### For Production (Future)
1. Initialize production Supabase schema:
   ```sql
   -- Go to Supabase dashboard SQL Editor
   -- Run: backend/scripts/schema_install.sql
   ```
2. Update backend/.env with production values
3. Deploy to production environment

---

## 🔧 Troubleshooting

### Services Not Starting
```bash
# Check logs
docker-compose logs -f

# Clean restart
docker-compose down
docker-compose up -d

# Reinitialize schema
./init-local-db.sh
```

### PostgREST Not Responding
```bash
# Restart to reload schema cache
docker-compose restart postgrest-test

# Verify API is accessible
curl http://localhost:3001/
```

### Backend Connection Issues
```bash
# Check environment
grep -E "^(SUPABASE|DATABASE)" backend/.env

# Should show localhost:3001 and localhost:54321

# Restart backend
pkill -f "uvicorn src.agent.main"
sleep 2
cd backend && uv run uvicorn src.agent.main:app --reload
```

### Port Conflicts
```bash
# Find what's using a port
lsof -i :3001     # PostgREST
lsof -i :54321    # PostgreSQL
lsof -i :8001     # Backend API

# Kill if needed
pkill -f "postgrest|postgres|uvicorn"
```

---

## 📖 Documentation Files

- **Main Setup:** [supabase/README.md](supabase/README.md)
- **Security Guide:** [SECURITY_ENV_GUIDE.md](SECURITY_ENV_GUIDE.md)
- **Database Schema:** [backend/scripts/schema_install.sql](backend/scripts/schema_install.sql)

---

## ✨ Key Features Implemented

✅ **Environment Isolation**
- Test and production completely separate
- Different ports, databases, credentials
- No risk of production data corruption during testing

✅ **Automated Initialization**
- Docker containers auto-start on first run
- Schema automatically installed on startup
- Full database setup in one command

✅ **Security Best Practices**
- Production credentials secured and gitignored
- Test credentials use safe dummy values
- .gitignore protects all secret files
- Comprehensive security documentation

✅ **Developer Experience**
- Simple startup script: `./start-local.sh`
- Connection verification: `./test-connection.sh`
- Clear error messages with fixes
- Health checks and diagnostics included

✅ **Complete Integration**
- Backend automatically configured for local testing
- LLM providers (DeepSeek, Groq, OpenAI) configured
- Web search (Tavily) enabled
- Embedding service ready

---

## 📞 Support Resources

For detailed information:
- Configuration: See [SECURITY_ENV_GUIDE.md](SECURITY_ENV_GUIDE.md)
- Local setup: See [supabase/README.md](supabase/README.md)
- Database schema: See [backend/scripts/schema_install.sql](backend/scripts/schema_install.sql)
- Production deployment: Contact repository owner

---

**Implementation Status: ✅ COMPLETE**

All systems operational. Ready for testing!
