# Deployment Workflow - Safe Multi-Service Deployment for Render

This document describes the safe, repeatable process for deploying Vecinita services on Render, with emphasis on zero-downtime deploys, data safety, and coordinated multi-service updates.

## Table of Contents

1. [Deployment Order](#deployment-order-first-time-setup)
2. [Ongoing Deployments](#ongoing-deployments-subsequent-deploys)
3. [Schema Changes](#handling-schema-changes-migrations)
4. [Zero-Downtime Strategy](#zero-downtime-strategy)
5. [Rollback Procedures](#rollback-procedures)
6. [Monitoring Deployments](#monitoring-deployments)
7. [Multi-Repo Coordination](#multi-repo-coordination)
8. [Troubleshooting](#troubleshooting)

---

## Deployment Order (First-Time Setup)

**Goal:** Establish all infrastructure and services in a working state, avoiding broken dependencies.

### Phase 1: Infrastructure

1. **Create Render Database**
   - Name: `vecinita-postgres`
   - Region: Virginia (same as services)
   - Plan: basic-256mb or higher depending on load
   - **Check:** Connect externally and verify tables are created (bootstrapping happens on agent startup)

2. **Create Environment Groups**
   - Name: `app-shared` with shared secrets and infrastructure bindings
   - Name: `agent-config` with agent-specific settings
   - Name: `gateway-config` with gateway-specific settings
   - Name: `frontend-config` with frontend URLs and timeouts
   - **Check:** All groups appear in Render dashboard with correct values

### Phase 2: Backend Services

3. **Deploy Agent Service** (`vecinita-agent`)
   - Template: Web service, Virginia region, Docker build
   - Port: 10000
   - **Pre-deploy command:** (empty for now; migrations via startup script)
   - Health check path: `/health`
   - **Check:** `curl https://vecinita-agent.onrender.com/health` returns 200 (may be slow first deploy)

4. **Deploy Gateway Service** (`vecinita-gateway`)
   - Depends on: Agent (via AGENT_SERVICE_URL binding)
   - Requires: `fromService: vecinita-agent` binding in render.yaml
   - Health check path: `/health`
   - **Check:** `curl https://vecinita-gateway.onrender.com/health` returns 200

### Phase 3: Frontend

5. **Deploy Frontend Service** (`vecinita-frontend`)
   - Depends on: Nothing (gateway can be live later)
   - Port: 10000
   - Build command: `npm ci && npm run build` (Vite)
   - Health check path: `/` (serves index.html)
   - **Check:** `https://vecinita-frontend.onrender.com` loads chat UI

### Phase 4: Verification

6. **End-to-End Test**
   ```bash
   # 1. Frontend loads
   curl https://vecinita-frontend.onrender.com/
   
   # 2. Frontend can reach gateway (VITE_GATEWAY_URL is set correctly)
   # Check browser console at https://vecinita-frontend.onrender.com
   # Should not have CORS errors or 404s
   
   # 3. Ask a question via gateway
   curl "https://vecinita-gateway.onrender.com/api/v1/ask?question=hello"
   
   # 4. Verify agent received it (check logs)
   ```

---

## Ongoing Deployments (Subsequent Deploys)

**Goal:** Update services safely without downtime, respecting data consistency.

### Standard Deployment Flow

```
1. Developer commits code to main branch
   ↓
2. Code changes land in specific service repo
   ↓
3. CI/CD triggers Render deploy via webhook
   ↓
4. Pre-deploy script runs (migrations, validation)
   ↓
5. New instances boot
   ↓
6. Health checks pass → Render considers deploy successful
   ↓
7. Old instances gradually drained
   ↓
8. Traffic fully switched to new instances
```

### Manual Deploy Trigger

If using `autoDeployTrigger: off` in render.yaml:

```bash
# Push to the configured branch (e.g., main)
git push origin main

# OR manually trigger in Render dashboard
# Service → Manual Deploy → Select branch → Deploy
```

### Monitoring During Deploy

```bash
# 1. Watch Render Events tab for deploy progress
# 2. Check new instance health:
curl https://vecinita-gateway.onrender.com/health
# Should return 200 within 30-60 seconds

# 3. Check logs for errors:
# Render dashboard → Service → Logs
```

---

## Handling Schema Changes (Migrations)

**CRITICAL:** Schema changes must be backward-compatible to avoid downtime.

### Safe Pattern

1. **Write backward-compatible migration:**
   - ADD columns with DEFAULT values (don't DROP)
   - ADD new tables, don't delete existing ones
   - Add new indexes or views, don't change existing query patterns

   ```sql
   -- ✅ SAFE (can run with old code)
   ALTER TABLE documents ADD COLUMN summary TEXT DEFAULT '';
   CREATE INDEX idx_new_field ON documents(new_field);
   
   -- ❌ UNSAFE (breaks queries using old column)
   ALTER TABLE documents DROP COLUMN old_field;
   ```

2. **Run migration before deploying code that needs new schema:**
   ```
   Step 1: Deploy agent with pre-deploy migration (adds column SUMMARY)
   Step 2: Deploy agent code that uses SUMMARY
   ```

3. **In pre-deploy script:**
   - Agent service ONLY runs `alembic upgrade head`
   - Gateway service does NOT run migrations (avoids race condition)
   - Workers do NOT run migrations

4. **Create migration file:**
   ```bash
   # In backend/scripts/migrations/
   cat > versions/20260407_add_summary.py << 'EOF'
   """Add document summary column"""
   
   from alembic import op
   import sqlalchemy as sa
   
   def upgrade():
       op.add_column('documents', sa.Column('summary', sa.String(), nullable=True, server_default=''))
   
   def downgrade():
       # Avoid downgrade if possible; just document rollback procedure
       pass
   EOF
   ```

5. **Test migration locally:**
   ```bash
   # Simulate with docker-compose.render-parity.yml
   docker-compose -f docker-compose.render-parity.yml down -v
   docker-compose -f docker-compose.render-parity.yml up -d
   # Agent startup should run migration automatically
   curl http://localhost:10000/db-info  # Check if migration took effect
   ```

### Example: Adding a New Column Safely

```
Iteration 1 (commit 1):
  ├─ Pre-deploy: ALTER TABLE documents ADD COLUMN summary TEXT DEFAULT '';
  └─ Code: Still doesn't use summary; query still works on old schema

Iteration 2 (commit 2):
  ├─ Pre-deploy: (no migration needed)
  └─ Code: Now reads/writes summary column

Iteration 3 (commit 3, optional cleanup):
  ├─ Pre-deploy: ALTER TABLE documents DROP COLUMN old_column;
  └─ Code: Doesn't reference old_column
```

This way, rollback at any point doesn't break queries.

---

## Zero-Downtime Strategy

### How Render Achieves Zero-Downtime Deploys

1. **Healthy instance check:**
   - Render starts NEW instance
   - Waits for `/health` to return 200
   - Only then switches traffic to new instance

2. **Grace period for cleanup:**
   - Old instance receives SIGTERM
   - Has up to 60 seconds to finish requests
   - Then old instance is terminated

3. **If health check fails:**
   - New instance is unhealthy (e.g., `/health` returns 500)
   - Render **cancels** the deploy
   - Old instances continue serving

### Your Responsibility

1. **Health check must be real:**
   ```python
   # ✅ GOOD (actually checks critical dependencies)
   @app.get("/health")
   async def healthz():
       # Check database connectivity
       try:
           result = await db.execute("SELECT 1")
       except Exception as e:
           return JSONResponse({"status": "unhealthy", "error": str(e)}, status_code=500)
       return JSONResponse({"status": "ok"})
   
   # ❌ BAD (just returns "ok" without checking anything)
   @app.get("/health")
   async def healthz():
       return JSONResponse({"status": "ok"})
   ```

2. **Connections must close gracefully:**
   ```python
   # Ensure connection pools drain requests before shutdown
   @app.on_event("shutdown")
   async def on_shutdown():
       await db.close()
       # Wait for in-flight requests to complete (SIGTERM timeout)
   ```

3. **Startup must be idempotent:**
   ```python
   # If service starts twice, must not corrupt state
   # E.g., don't create duplicate records if migration already ran
   if not schema_exists():
       run_migration()  # OK: idempotent
   ```

### Testing Zero-Downtime Locally

```bash
# Simulate with old and new container
docker-compose -f docker-compose.render-parity.yml up -d

# In one terminal, watch requests
while true; do
  curl -s http://localhost:8080/health
  sleep 1
done

# In another terminal, trigger deploy
docker-compose -f docker-compose.render-parity.yml restart vecinita-gateway

# Verify: curl returns 200 the entire time (may be 1-2 second pause)
```

---

## Rollback Procedures

### Scenario 1: Deploy Completed, But Service is Broken

**Symptoms:** Deployed 5 minutes ago, health check passes, but gateway returns 500

**Procedure:**
1. Revert code commit
2. Push to main branch (triggers new deploy)
3. Render redeploys with previous working version
4. Takes 2-5 minutes

**Prevention:** Test in staging first, or use `autoDeployTrigger: off` and manually test before deploy

### Scenario 2: Deploy Never Completed

**Symptoms:** New instance health check fails, Render canceled deploy, old version still running

**Procedure:**
1. Check Render events tab for error message
2. Review service logs for crash reason
3. Fix code locally, push commit
4. Render automatically redeploys (if autoDeployTrigger is on), or manually trigger

### Scenario 3: Database Migration Failed

**Symptoms:** Pre-deploy script crashed, agent won't start

**Procedure:**
1. **Render keeps old instances running** (new instances couldn't boot)
2. Check agent logs: `Render dashboard → Service → Logs`
3. Look for SQL errors or migration issues
4. Fix migration script or alembic config
5. Push commit → Render redeploys and runs migration again

### Scenario 4: Secret/Env Var Missing

**Symptoms:** Service starts but immediately fails because API key is unset

**Procedure:**
1. Add missing env var to Render dashboard (app-shared group or service-specific)
2. Redeploy service (or manually restart)
3. Does NOT require code change; just env update

---

## Monitoring Deployments

### Real-Time Deploy Monitoring

**Dashboard (Recommended):**
1. Open Render dashboard
2. Select service (e.g., vecinita-gateway)
3. Watch "Events" tab for deploy progress
4. Click through to "Logs" if needed

**CLI (if using render CLI):**
```bash
rendercli service list
rendercli service get --name vecinita-gateway
rendercli logs --service vecinita-gateway --follow
```

**Health Check Endpoints:**
```bash
# Before deploy (old version)
curl -I https://vecinita-gateway.onrender.com/health

# During deploy (may see 502 Bad Gateway for a few seconds)
curl -I https://vecinita-gateway.onrender.com/health

# After deploy (new version)
curl -I https://vecinita-gateway.onrender.com/health
# Should see immediate 200 OK
```

### Key Metrics to Watch

| Metric | Healthy | Unhealthy |
|--------|---------|-----------|
| Deploy duration | 2–5 minutes | > 10 minutes (stuck) |
| Health check delay | First check within 30s | No health response after 1 min |
| Service availability | 200 OK from `/health` | 500, timeout, no response |
| Log output | Startup logs visible | No logs, or error stack traces |

---

## Multi-Repo Coordination

Vecinita comprises multiple GitHub repositories. Deployment must be coordinated:

| Repository | Service | Status | Deploy Trigger |
|------------|---------|--------|----------------|
| acadiagit/vecinita (this repo) | Agent, Gateway, Frontend | Main deployments | Manual or CI/CD webhook |
| joseph-c-mcguire/Vecinitafrontend | Chat Frontend | (if separate) | Own CI/CD |
| Math-Data-Justice-Collaborative/vecinita-data-management | Data Mgmt API | Separate service | Own CI/CD |
| Math-Data-Justice-Collaborative/vecinita-scraper | Scraper | Modal deploy | Own CI/CD to Modal |
| Math-Data-Justice-Collaborative/vecinita-embedding | Embedding | Modal deploy | Own CI/CD to Modal |
| Math-Data-Justice-Collaborative/vecinita-model | Model | Modal deploy | Own CI/CD to Modal |

### Coordinated Deployment

**Scenario:** You add a new embedding API parameter that agent must use

1. **Scraper/Embedding repo:** Add new parameter to `/embed` endpoint
2. **This repo (agent):** Add code to pass new parameter in the request
3. **This repo (render.yaml):** Update VECINITA_EMBEDDING_API_URL if endpoint changed

**Deployment order:**
```
Step 1: Deploy embedding service to Modal (new endpoint)
Step 2: Wait for endpoint to be live (5–10 min)
Step 3: Deploy agent to Render (now uses new parameter)
```

If deployed in reverse order:
- Agent tries to use new parameter before Modal endpoint supports it
- Embedding calls fail
- Agent errors out

### Multi-Repo Release Orchestration

For synchronized multi-repo releases, use `.github/workflows/multi-repo-release-orchestrator.yml` (if present) or:

```bash
# Manual coordinated deploy:
cd vecinita && git push origin main  # Triggers Render deploy
cd vecinita-embedding && git push origin main  # Triggers Modal deploy
cd vecinita-scraper && git push origin main  # Triggers Modal deploy
# Wait for all to complete (each 5–10 minutes)
```

---

## Troubleshooting

### Deployment Fails: Pre-Deploy Script Error

**Error in logs:** `alembic: error: No such file or directory`

**Cause:** Migration file not found or alembic config broken

**Fix:**
```bash
# Locally, verify migration setup
cd backend
alembic upgrade head  # Test locally first
# If works locally, the issue is Render environment
```

**Prevention:** Test pre-deploy script in docker-compose before pushing

### New Instance is Unhealthy

**Error in logs:** `[ERROR] Failed to connect to database`

**Cause:** DATABASE_URL binding didn't work or database credentials wrong

**Fix:**
1. Check Render dashboard → app-shared env group → DATABASE_URL
2. Verify it's not empty
3. Test connection: `psql $(echo $DATABASE_URL | sed 's/postgresql:\/\///') -c "SELECT 1"`
4. If still failing, re-deploy with `--force`

### Gateway Can't Reach Agent

**Error in logs:** `ConnectError: Failed to connect to http://vecinita-agent:10000`

**Cause:** Agent service not healthy OR AGENT_SERVICE_URL binding didn't work

**Fix:**
1. Check if agent is healthy: Render dashboard → vecinita-agent → health
2. Verify AGENT_SERVICE_URL in gateway env: `Render dashboard → vecinita-gateway → Settings → Environment`
3. Should be `http://vecinita-agent:10000` (or `.onrender.internal`)
4. If wrong, redeploy gateway after fixing env

### Stuck Deployment

**Symptom:** Deploy shows "In Progress" for > 10 minutes

**Cause:** Health check endpoint not responding or service in infinite loop

**Fix:**
1. Cancel deploy: Render dashboard → Service → Cancel Deploy
2. Check logs for infinite loops or stuck processes
3. Redeploy with fix

---

## Deployment Checklist

Use this before each production deploy:

```
Pre-Deploy (Local)
  [ ] Code reviewed and tested locally
  [ ] Migrations tested with docker-compose.render-parity.yml
  [ ] No secrets committed to render.yaml
  [ ] All dependencies updated in requirements.txt / package.json
  [ ] Health check endpoint works: curl http://localhost:8080/health
  [ ] Tests pass: pytest, npm test

Pre-Deploy (Staging)
  [ ] Deploy to staging environment first (if have staging blueprint)
  [ ] Run smoke tests: E2E test that asks a question
  [ ] Monitor logs for errors
  [ ] Check database for corruption

Pre-Deploy (Production)
  [ ] Backup database (Render auto-backs up, but check last backup time)
  [ ] Notify team: "Deploying X at Y time"
  [ ] Have rollback commit ready if needed

Deploy
  [ ] Push to main branch (or manually trigger in Render)
  [ ] Watch Render events for progress
  [ ] Monitor /health endpoint from external tool

Post-Deploy
  [ ] Test CLI: curl https://vecinita-gateway.onrender.com/health
  [ ] Test frontend: https://vecinita-frontend.onrender.com
  [ ] Ask a test question via frontend
  [ ] Monitor logs for errors: Render dashboard → Logs
  [ ] If issue found: Proceed to Rollback section

Rollback (if needed)
  [ ] Revert problematic commit
  [ ] Push to main (triggers new deploy)
  [ ] Monitor new deploy progress
  [ ] Verify /health returns 200
```

---

## Contacts & Escalation

| Issue | Owner | Contact |
|-------|-------|---------|
| Render service config | DevOps / Backend lead | @owner in Slack |
| Database connectivity | DevOps | @owner in Slack |
| Modal service down | ML/Compute team | @ml-team in Slack |
| CORS issues | Frontend + Gateway lead | @frontend @backend in Slack |
| Emergency rollback needed | DevOps lead | Immediate @owner call |

---

## Related Documentation

- [SERVICE_BOUNDARIES.md](SERVICE_BOUNDARIES.md) — Which service depends on which
- [ENV_GROUPS_CONTRACT.md](ENV_GROUPS_CONTRACT.md) — Environment variable ownership and governance
- [LOCAL_DEV_SETUP.md](LOCAL_DEV_SETUP.md) — Mirroring Render locally
- [Render Deployment Guides](https://render.com/docs/deploy-service)
