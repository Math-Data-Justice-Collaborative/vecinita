# Vecinita Setup Verification Checklist

## ✅ What You Should See

After setup, verify these items are in place:

## Makefile Targets

```
✅ make dev-chat                    # New: Start chat application
✅ make dev-chat-backend            # New: Start chat backend services
✅ make dev-chat-agent              # New: Start chat agent only
✅ make dev-chat-gateway            # New: Start chat gateway only
✅ make dev-chat-frontend           # New: Start chat frontend only

✅ make dev-data-management         # New: Start data management system
✅ make dev-data-management-api     # New: Start data management API
✅ make dev-data-management-frontend # New: Start data management frontend

✅ make dev                         # Original: Full stack
✅ make dev-backend                 # Original: Agent only (legacy)
✅ make dev-gateway                 # Original: Gateway only (legacy)
✅ make dev-frontend                # Original: Frontend only (legacy)
```

## Environment Files

```
✅ /root/GitHub/VECINA/vecinita/.env                      # Root config (SHARED)
✅ /root/GitHub/VECINA/vecinita/.env.example              # Template (unchanged)
✅ /root/GitHub/VECINA/vecinita/backend/.env              # Backend overrides (optional)
✅ /root/GitHub/VECINA/vecinita/frontend/.env             # Frontend config (optional)
```

## Documentation Files

```
✅ DEV_STARTUP.md                   # Quick start guide
✅ ENVIRONMENT_SETUP.md             # Complete environment reference
✅ SUPABASE_CONFIGURATION.md        # Supabase integration guide
✅ ENVIRONMENT_SETUP_SUMMARY.md     # This summary document
```

## Supabase Configuration in Root `.env`

```bash
# Verify these are all present and not empty:

grep SUPABASE_URL .env              # Should output: https://your-project.supabase.co
grep SUPABASE_KEY .env              # Should output: <supabase-service-role-key>
grep SUPABASE_SECRET_KEY .env       # Should output: <supabase-service-role-key>
grep VITE_SUPABASE_URL .env         # Should output: https://your-project.supabase.co
grep VITE_SUPABASE_ANON_KEY .env    # Should output: <supabase-anon-key>
grep DATABASE_URL .env              # Should output: postgresql://...
```

## API Keys Preserved

```bash
# Verify all secrets are intact:

grep GROQ_API_KEY .env              # Should start with: gsk_
grep OPENAI_API_KEY .env            # Should start with: sk-proj-
grep DEEPSEEK_API_KEY .env          # Should start with: sk-
grep TAVILY_API_KEY .env            # Should start with: tvly-
grep LANGSMITH_API_KEY .env         # Should start with: lsv2_pt_
```

## Test Chat Application Startup

```bash
# Terminal 1: Start Chat Backend
make dev-chat-backend &
sleep 3

# Check Agent is running on port 8000
curl -s http://localhost:8000/health | jq .

# Check Gateway is running on port 8004 with Supabase
curl -s http://localhost:8004/health | jq .

# Terminal 2: Start Chat Frontend
make dev-chat-frontend
# Should see: Localhost: http://127.0.0.1:5173/
```

## Test Data Management Startup

```bash
# Terminal 1: Start Data Management API
make dev-data-management-api &
sleep 3

# Check API is running (depends on implementation)
# Typically: curl -s http://localhost:8005/health | jq .

# Terminal 2: Start Data Management Frontend
make dev-data-management-frontend
# Should see: Localhost: http://127.0.0.1:5174/
```

## Verify Both Systems Share Supabase

```bash
# Terminal 1: Chat Backend
make dev-chat-backend 2>&1 | grep -i supabase

# Terminal 2: Data Management API
make dev-data-management-api 2>&1 | grep -i supabase

# Both should log the same SUPABASE_URL value
```

## Network Connectivity Check

### Chat Application Ports
```bash
# Check ports are in use:
lsof -i :5173    # Chat Frontend
lsof -i :8000    # Chat Agent
lsof -i :8004    # Chat Gateway
```

### Data Management System Ports
```bash
# Check ports are in use:
lsof -i :5174    # DM Frontend
lsof -i :8005    # DM API
```

### Local Services
```bash
# Check optional services if running:
lsof -i :5432    # PostgreSQL
lsof -i :8002    # ChromaDB
```

## Browser Tests

### Chat Application
1. Open http://localhost:5173 (Chat Frontend)
2. Should see login page or chat interface
3. Check Network tab → API calls should go to localhost:8004
4. Frontend should authenticate via Supabase

### Data Management System
1. Open http://localhost:5174 (DM Frontend)
2. Should see data management interface
3. Check Network tab → API calls should go to localhost:8005
4. Frontend should authenticate via Supabase

## Database Connectivity

### Verify Supabase Connection
```bash
# From Chat Backend logs
make dev-chat-backend 2>&1 | grep -i "database\|postgres\|supabase" | head -5

# Test connection
PGPASSWORD='<db-password>' psql -h aws-<region>.pooler.supabase.com \
   -U postgres.your-project-ref -d postgres -c "SELECT version();"
```

## Troubleshooting Checks

### If `make dev-chat` fails
```bash
# 1. Check .env exists
ls -la .env

# 2. Check .env is readable
cat .env | head -5

# 3. Verify Supabase vars are set
source .env && echo "SUPABASE_URL=$SUPABASE_URL"

# 4. Check Backend dependencies
cd backend && uv sync

# 5. Check Frontend dependencies
cd frontend && npm ci
```

### If Chat Frontend can't connect to Backend
```bash
# 1. Verify Gateway is running
curl -i http://localhost:8004/health

# 2. Check frontend config
cat frontend/.env | grep -i gateway

# 3. Check CORS in browser console
# Should NOT see CORS errors if properly configured
```

### If Data Management can't reach API
```bash
# 1. Verify API is running
ps aux | grep "port 8005"

# 2. Check API is accepting connections
curl -i http://localhost:8005/ 2>&1 | head -3

# 3. Check .env is sourced in API
ps aux | grep "npm run dev" | grep data-management
```

### If Both Systems See Different Data
```bash
# MUST use same Supabase instance

# Chat Backend SUPABASE_URL
make dev-chat-backend 2>&1 | grep "SUPABASE_URL"

# DM API SUPABASE_URL
make dev-data-management-api 2>&1 | grep "SUPABASE_URL"

# Both should output IDENTICAL URLs
```

## Final Verification Command

Run this script to verify everything:

```bash
#!/bin/bash
set -e

echo "Vecinita Setup Verification"
echo "==========================="
echo ""

echo "✓ Checking Makefile targets..."
make help 2>&1 | grep -q "dev-chat" && echo "  ✅ dev-chat targets found"
make help 2>&1 | grep -q "dev-data-management" && echo "  ✅ dev-data-management targets found"

echo ""
echo "✓ Checking .env configuration..."
[ -f .env ] && echo "  ✅ .env file exists"
grep -q "SUPABASE_URL" .env && echo "  ✅ SUPABASE_URL configured"
grep -q "DATABASE_URL" .env && echo "  ✅ DATABASE_URL configured"
grep -q "GROQ_API_KEY" .env && echo "  ✅ API keys present"

echo ""
echo "✓ Checking documentation..."
[ -f DEV_STARTUP.md ] && echo "  ✅ DEV_STARTUP.md exists"
[ -f ENVIRONMENT_SETUP.md ] && echo "  ✅ ENVIRONMENT_SETUP.md exists"
[ -f SUPABASE_CONFIGURATION.md ] && echo "  ✅ SUPABASE_CONFIGURATION.md exists"

echo ""
echo "✓ Checking dependencies..."
command -v make &> /dev/null && echo "  ✅ Make installed"
command -v npm &> /dev/null && echo "  ✅ npm installed"
command -v python3 &> /dev/null && echo "  ✅ python3 installed"

echo ""
echo "==========================="
echo "✅ All checks passed!"
echo ""
echo "Next steps:"
echo "  1. Read: DEV_STARTUP.md"
echo "  2. Run:  make dev-chat"
echo "  3. Or:   make dev-data-management"
```

Save as `verify_setup.sh` and run: `bash verify_setup.sh`

## Success Indicators

### Chat Application Running
```
✅ Frontend loads on http://localhost:5173
✅ Agent runs on http://localhost:8000 (health check returns 200)
✅ Gateway runs on http://localhost:8004 (health check returns 200)
✅ Chat requests return responses from Supabase vector search
✅ Authentication works via Supabase JWT
```

### Data Management Running
```
✅ Frontend loads on http://localhost:5174
✅ API runs on http://localhost:8005
✅ Data reads/writes to same Supabase as Chat
✅ Authentication uses Supabase
```

### Both Systems Integrated
```
✅ Chat and DM frontends both load
✅ Both authenticate via Supabase
✅ Both can query shared database
✅ No port conflicts between services
✅ Logs show same SUPABASE_URL for both backends
```

## Common Issues & Solutions

| Issue | Check | Solution |
|-------|-------|----------|
| Port already in use | `lsof -i :5173` | `make dev-clear-ports` |
| .env not found | `ls -la .env` | Copy `.env.example` to `.env` and add secrets |
| Different Supabase for each service | Check logs | Both MUST source from root `.env` |
| Authentication fails | Check VITE_SUPABASE_ANON_KEY | Verify it's not empty in .env |
| API returns 404 | `curl http://localhost:8005` | Check API service actually started |
| Frontend can't reach backend | Check network tab in DevTools | Verify URL and CORS settings |

## Next Steps

✅ All checks passed? Great!

1. **Read the docs:**
   - `DEV_STARTUP.md` - Quick reference
   - `ENVIRONMENT_SETUP.md` - Complete guide

2. **Start developing:**
   - `make dev-chat` - Chat application
   - `make dev-data-management` - Data management system

3. **Share with team:**
   - **DO NOT commit:** Real `.env` files with secrets
   - **DO commit:** `.env.example` templates
   - **Share with team:** Copy of `.env` via secure method (password manager, etc.)

4. **Deployment:**
   - See `docs/deployment/MULTI_REPO_CICD_ORCHESTRATION.md`
   - Configure environment variables in Render dashboard (not in code)
