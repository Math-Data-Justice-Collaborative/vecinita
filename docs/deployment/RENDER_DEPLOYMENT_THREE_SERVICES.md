# Render Deployment Guide - Three Free-Tier Services

## Architecture Overview

This deployment uses **three separate free-tier Render services**:

1. **vecinita-embedding** (Free tier, 512MB) - Embedding service
2. **vecinita-agent** (Free tier, 512MB) - FastAPI agent
3. **vecinita-scraper** (Free tier cron) - Background scraper
4. **vecinita-frontend** (Free tier, 512MB) - React frontend

Each service runs independently on Render's **free tier** (512MB limit).

---

## Pre-Deployment Checklist

- [ ] Render account created (https://render.com)
- [ ] GitHub repository connected to Render
- [ ] Supabase project created and credentials ready
- [ ] GROQ API key (or alternative LLM) ready
- [ ] HuggingFace account created (free)

---

## Step 1: Deploy Embedding Service

### 1.1 Create New Web Service

```bash
# Via Render Dashboard:
# 1. Go to https://dashboard.render.com
# 2. Click "+ New"
# 3. Select "Web Service"
```

### 1.2 Configure Embedding Service

| Setting | Value |
|---------|-------|
| **Name** | `vecinita-embedding` |
| **Repository** | Your GitHub repo |
| **Branch** | `main` (or your deploy branch) |
| **Runtime** | Docker |
| **Region** | Virginia (or closest to you) |
| **Plan** | **Free** |
| **Dockerfile path** | `backend/Dockerfile.embedding` |
| **Build command** | (auto-detected) |
| **Start command** | (auto-detected) |

### 1.3 Add Environment Variables

In Render Dashboard → `vecinita-embedding` → Environment:

```
PORT=8001
PYTHONUNBUFFERED=1
HF_HOME=/tmp/huggingface_cache
```

### 1.4 Set Health Check Path

- Path: `/health`
- Interval: 30s
- Timeout: 10s

### 1.5 Deploy

Click **Deploy**. Wait for green checkmark. Note the URL (e.g., `https://vecinita-embedding.onrender.com`).

---

## Step 2: Deploy Agent Service

### 2.1 Create New Web Service

```
Go to https://dashboard.render.com → "+ New" → "Web Service"
```

### 2.2 Configure Agent Service

| Setting | Value |
|---------|-------|
| **Name** | `vecinita-agent` |
| **Repository** | Same GitHub repo |
| **Branch** | `main` |
| **Runtime** | Docker |
| **Region** | Virginia |
| **Plan** | **Free** |
| **Dockerfile path** | `backend/Dockerfile` |

### 2.3 Add Environment Variables

In Render Dashboard → `vecinita-agent` → Environment:

```
PORT=10000
PYTHONUNBUFFERED=1
TF_ENABLE_ONEDNN_OPTS=0
EMBEDDING_SERVICE_URL=https://vecinita-embedding.onrender.com
```

**Add these as secrets** (click "Add Secret"):
- `SUPABASE_URL` - From Supabase Dashboard
- `SUPABASE_KEY` - From Supabase Dashboard  
- `GROQ_API_KEY` - From groq.com
- `OPENAI_API_KEY` (optional)
- `DEEPSEEK_API_KEY` (optional)
- `LANGSMITH_API_KEY` (optional, for tracing)

### 2.4 Set Health Check Path

- Path: `/health`

### 2.5 Deploy

Click **Deploy**. Wait for green checkmark. Note the URL (e.g., `https://vecinita-agent.onrender.com`).

---

## Step 3: Deploy Scraper Service (Optional)

### 3.1 Create Cron Job

```
Go to https://dashboard.render.com → "+ New" → "Background Worker"
```

### 3.2 Configure Scraper

| Setting | Value |
|---------|-------|
| **Name** | `vecinita-scraper` |
| **Repository** | Same GitHub repo |
| **Branch** | `main` |
| **Runtime** | Docker |
| **Region** | Virginia |
| **Plan** | **Free** |
| **Dockerfile path** | `backend/Dockerfile.scraper` |

### 3.3 Add Environment Variables

```
PYTHONUNBUFFERED=1
EMBEDDING_SERVICE_URL=https://vecinita-embedding.onrender.com
```

**Add as secrets:**
- `SUPABASE_URL`
- `SUPABASE_KEY`
- `DATABASE_URL` (if using PostgreSQL)

### 3.4 Set Schedule (Optional)

```
0 2 * * *  # Daily at 2 AM UTC
```

---

## Step 4: Deploy Frontend Service

### 4.1 Create Web Service

```
Go to https://dashboard.render.com → "+ New" → "Web Service"
```

### 4.2 Configure Frontend

| Setting | Value |
|---------|-------|
| **Name** | `vecinita-frontend` |
| **Repository** | Same GitHub repo |
| **Branch** | `main` |
| **Runtime** | Docker |
| **Region** | Virginia |
| **Plan** | **Free** |
| **Dockerfile path** | `frontend/Dockerfile` |

### 4.3 Add Environment Variables

```
VITE_BACKEND_URL=https://vecinita-agent.onrender.com
```

### 4.4 Deploy

Click **Deploy**.

---

## Post-Deployment Verification

### 1. Check Service Health

```bash
# Embedding service
curl https://vecinita-embedding.onrender.com/health

# Agent service
curl https://vecinita-agent.onrender.com/health

# Frontend
curl https://vecinita-frontend.onrender.com
```

All should return 200 OK.

### 2. Test Agent Endpoint

```bash
curl "https://vecinita-agent.onrender.com/ask?question=test"
```

Should return a JSON response with an answer.

### 3. Test Embedding Service

```bash
curl -X POST https://vecinita-embedding.onrender.com/embed \
  -H "Content-Type: application/json" \
  -d '{"text": "test"}'
```

Should return:
```json
{
  "embedding": [0.123, -0.456, ...],
  "dimension": 384,
  "model": "sentence-transformers/all-MiniLM-L6-v2"
}
```

### 4. Visit Frontend

Go to: `https://vecinita-frontend.onrender.com`

Should show the web UI.

---

## Monitoring

### View Logs

In Render Dashboard:
- Click service name
- Click "Logs" tab
- Search for errors or issues

### Monitor Resource Usage

Free tier specs:
- **CPU:** Shared, ~0.5 CPU
- **Memory:** 512MB limit
- **Storage:** Ephemeral (data lost on restart)
- **Uptime:** ~99% (10-15 min/month shutdown for maintenance)

### Common Issues

| Issue | Solution |
|-------|----------|
| Service won't start | Check logs, verify env vars, ensure Dockerfile path correct |
| Embedding timeout | Increase timeout, or the HF model is still loading (first request ~20s) |
| Agent can't reach embedding | Verify `EMBEDDING_SERVICE_URL` in agent env vars |
| Memory limit exceeded | Embedding service uses ~400MB on first load, agent ~250MB, normal |
| Service restarts frequently | Check memory usage, may be hitting 512MB limit |

---

## Performance Expectations

### Cold Start Times (First Request After Deploy)

- **Embedding Service:** ~20-30s (HuggingFace model download & cache)
- **Agent Service:** ~5-10s
- **Subsequent Requests:** ~100-200ms for agent, ~200-300ms for embedding

### Memory Usage

| Service | Usage | Note |
|---------|-------|------|
| Embedding | ~350-400MB | HuggingFace model caching |
| Agent | ~200-250MB | LangChain + frameworks |
| Total | ~550-650MB | Split across 2 free services = OK |

### Free Tier Limits

- **Build time:** 100 minutes/month
- **Invocations:** Unlimited (cron) or always-on (web)
- **Storage:** Ephemeral (no persistent disk)

---

## Production Tips

1. **Scaling:** If you hit memory limits, upgrade to Paid plan ($7/month per service)

2. **Data Persistence:** Use Supabase PostgreSQL for data (already doing this)

3. **Caching:** Embedding results are cached by Supabase, not re-computed

4. **Cost Optimization:**
   - Embedding service: Always running (free tier OK)
   - Agent service: Always running (free tier OK)  
   - Scraper: Cron job (free tier OK, runs once per day)
   - Frontend: Always running (free tier OK)
   - **Total cost: $0**

5. **Monitoring:**
   - Set up Sentry for error tracking (free tier available)
   - Monitor Supabase query performance
   - Check HuggingFace API rate limits (30k req/month free)

---

## Disaster Recovery

### If a Service Goes Down

1. Check Render Dashboard status
2. Click service → "Manual Deploy"
3. Check logs for errors
4. If persistent, verify environment variables

### If You Need to Rollback

1. Go to service → "Deploys" tab
2. Find previous working deploy
3. Click "Redeploy"

### Backup Configuration

All config is in version control:
- `render.yaml` - Service definitions
- `docker-compose.yml` - Local equivalents
- `.env` - Secrets (in Render Dashboard)

---

## Next Steps

After deployment:

1. ✅ Verify all services are healthy
2. ✅ Test agent with real queries
3. ✅ Monitor logs for first 24 hours
4. ✅ Set up daily scraper schedule
5. ✅ Update documentation with live URLs

---

## Support

- **Render Docs:** https://render.com/docs
- **GitHub Issues:** Open an issue in your repo
- **Logs:** Always check Render Dashboard → Logs tab first
