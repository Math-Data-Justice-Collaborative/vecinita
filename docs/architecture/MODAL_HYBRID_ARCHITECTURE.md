# 🏗️ Hybrid Architecture: Modal + Traditional Hosting

**Optimal deployment strategy for Vecinita using Modal serverless for resource-intensive services**

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     PRODUCTION ARCHITECTURE                      │
└─────────────────────────────────────────────────────────────────┘

┌──────────────────────┐
│  Users / Browser     │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  Frontend (Vercel)   │  ← Static Site (Always-On, Edge CDN)
│  Port: 443 (HTTPS)   │
└──────────┬───────────┘
           │ HTTPS
           ▼
┌─────────────────────────────────────────┐
│  Agent Service (Render Web Service)     │  ← Always-On API
│  FastAPI + LangGraph Q&A                │
│  Port: 8000                             │
└─────┬──────────────┬────────────────────┘
      │              │
      │ HTTP         │ HTTPS
      ▼              ▼
┌──────────────┐   ┌────────────────────────────┐
│  Supabase    │   │  Modal Serverless          │  ← Auto-scaling
│  PostgreSQL  │   │  ┌──────────────────────┐  │
│  (Managed)   │   │  │ Embedding Service    │  │
│              │   │  │ • Scales to zero     │  │
│              │   │  │ • Auto-scales up     │  │
└──────────────┘   │  │ • Pay per use        │  │
                   │  └──────────────────────┘  │
                   │  ┌──────────────────────┐  │
                   │  │ Scraper Service      │  │
                   │  │ • Cron scheduled     │  │
                   │  │ • Batch processing   │  │
                   │  │ • Scales to zero     │  │
                   │  └──────────────────────┘  │
                   └────────────────────────────┘
```

---

## Service Placement Strategy

### ☁️ **Modal Serverless (Auto-Scaling)**

#### 1. Embedding Service ✅
**Why Modal:**
- CPU/memory intensive (loads 200MB+ ML model)
- Bursty traffic pattern (not always needed)
- Can scale to zero when idle
- Auto-scales during high demand
- Cold start acceptable (~3-5 seconds)

**Cost Savings:**
- Local/Render: ~$20-50/month (always-on)
- Modal: ~$5-15/month (pay-per-use)

**Deployment:**
```bash
./backend/scripts/deploy_modal.sh --embedding
```

#### 2. Scraper Service ✅
**Why Modal:**
- Runs on schedule (cron jobs)
- Very resource intensive during scraping
- Idle 95% of the time
- Batch processing workload
- Long-running tasks OK

**Cost Savings:**
- Local/Render: ~$30-60/month (needs 2GB RAM)
- Modal: ~$3-10/month (runs 1-2 hours/day)

**Deployment:**
```bash
./backend/scripts/deploy_modal.sh --scraper
```

---

### 🖥️ **Traditional Hosting (Always-On)**

#### 3. Agent Service (Render) ✅
**Why NOT Modal:**
- Needs low latency (<100ms response)
- Always-on for user queries
- Cold starts unacceptable for users
- Frequent access pattern

**Why Render:**
- Auto-scaling available
- Always-on with low latency
- Affordable ($7/month basic tier)
- Easy deployment

#### 4. Frontend (Vercel/Render) ✅
**Why NOT Modal:**
- Static site (HTML/CSS/JS)
- Best on edge CDN
- Needs ultra-low latency
- Always available

**Why Vercel:**
- Free tier generous
- Edge CDN globally distributed
- Auto-deploys from Git
- Built-in HTTPS

#### 5. Database (Supabase) ✅
**Why NOT Modal:**
- Persistent data storage
- Needs always-on availability
- Complex query optimization
- Managed backups required

**Why Supabase:**
- Free tier (500MB)
- Built-in PostgREST API
- Auto-scaling
- Managed backups

---

## Cost Comparison

### Traditional All-On-Render
```
Agent Service:      $25/month  (1GB RAM)
Embedding Service:  $50/month  (2GB RAM, always-on)
Scraper Service:    $50/month  (2GB RAM, always-on)
Frontend:           $0         (Vercel free)
Database:           $0         (Supabase free tier)
─────────────────────────────
TOTAL:              $125/month
```

### Hybrid Modal + Render (Recommended)
```
Agent Service:      $25/month  (Render, 1GB RAM)
Embedding Service:  $10/month  (Modal, pay-per-use)
Scraper Service:    $5/month   (Modal, scheduled runs)
Frontend:           $0         (Vercel free)
Database:           $0         (Supabase free tier)
─────────────────────────────
TOTAL:              $40/month  (68% savings!)
```

---

## Environment Configuration

> Modal is the current post-hoc embedding/reindex platform. The backend keeps URL/token abstraction so Cloud Run can replace Modal later by changing env values.

### Local Development (.env.local)
```env
# All services run locally in Docker
EMBEDDING_SERVICE_URL=http://localhost:8001
SCRAPER_SERVICE_URL=http://localhost:8002
SUPABASE_URL=http://localhost:3001
```

### Production (.env.prod)
```env
# Embedding and scraper on Modal serverless
EMBEDDING_SERVICE_URL=https://your-workspace--vecinita-embedding-web.modal.run
SCRAPER_SERVICE_URL=https://your-workspace--vecinita-scraper-web.modal.run
REINDEX_SERVICE_URL=https://your-workspace--vecinita-scraper-web.modal.run
EMBEDDING_SERVICE_AUTH_TOKEN=<shared-service-token>
REINDEX_TRIGGER_TOKEN=<shared-reindex-token>
REINDEX_CRON_SCHEDULE=0 2 * * 0
SUPABASE_URL=https://your-project.supabase.co
```

---

## Deployment Steps

### Step 1: Local Testing
```bash
# Test everything locally first
./setup.sh
# Verify at http://localhost:5173
```

### Step 2: Deploy Modal Services
```bash
# Install Modal CLI
pip install modal

# Authenticate
modal token new

# Deploy embedding service
./backend/scripts/deploy_modal.sh --embedding

# Deploy scraper service
./backend/scripts/deploy_modal.sh --scraper

# Or deploy both
./backend/scripts/deploy_modal.sh --all
```

**Note the URLs** that Modal provides after deployment.

### Step 3: Update Production Environment
```bash
# Edit .env.prod with Modal URLs
nano .env.prod

# Update these lines with your Modal URLs:
EMBEDDING_SERVICE_URL=https://your-actual-modal-url.modal.run
SCRAPER_SERVICE_URL=https://your-actual-modal-url.modal.run
REINDEX_SERVICE_URL=https://your-actual-modal-url.modal.run
```

### Step 4: Deploy Agent Service to Render
```bash
# Push to GitHub (triggers Render deployment)
git add .
git commit -m "Configure Modal serverless services"
git push

# Or deploy manually via Render dashboard
# See: docs/RENDER_DEPLOYMENT_THREE_SERVICES.md
```

### Step 5: Deploy Frontend
```bash
# If using Vercel:
cd frontend
vercel deploy --prod

# If using Render:
# Deploy via Render dashboard with frontend/ as root
```

---

## Monitoring & Management

### Modal Services

**View Logs:**
```bash
modal app logs vecinita-embedding
modal app logs vecinita-scraper
```

**Check Status:**
```bash
modal app list
```

**Update/Redeploy:**
```bash
./backend/scripts/deploy_modal.sh --embedding --force
```

### Agent Service (Render)

**View Logs:**
- Render Dashboard → Your Service → Logs

**Environment Variables:**
- Render Dashboard → Your Service → Environment
- Add `EMBEDDING_SERVICE_URL` with Modal URL

---

## Traffic Patterns & Scaling

### Embedding Service (Modal)
- **Cold Start:** 3-5 seconds (first request after idle)
- **Warm:** <200ms (subsequent requests)
- **Auto-scale:** Handles 10-100 concurrent requests
- **Idle:** Scales to zero after 5 minutes

### Scraper Service (Modal)
- **Trigger:** Weekly cron schedule (default: `0 2 * * 0`, Sunday 02:00 UTC)
- **Duration:** 30-120 minutes per run
- **Resources:** Scales up to needed RAM/CPU
- **Cost:** Only during active scraping

### Manual Reindex Trigger
- **Gateway endpoint:** `POST /api/v1/scrape/reindex`
- **Forwarding target:** `${REINDEX_SERVICE_URL}/reindex`
- **Auth:** `REINDEX_TRIGGER_TOKEN` propagated as `x-reindex-token`

### Agent Service (Render)
- **Always-On:** Zero cold start
- **Latency:** <100ms response time
- **Scaling:** Auto-scales with traffic
- **Cost:** Flat monthly rate

---

## Troubleshooting

### "Modal service timeout"
- Check Modal dashboard for errors
- Verify authentication: `modal token new`
- Check service logs: `modal app logs vecinita-embedding`

### "Embedding service unreachable"
- Verify Modal URL in .env.prod
- Test Modal endpoint: `curl https://your-modal-url.modal.run/health`
- Check Modal service is running: `modal app list`

### "High latency on first request"
- Expected: Modal cold start (3-5s)
- Solution: Keep-alive ping every 4 minutes
- Or: Use Render for embedding if latency critical

---

## Best Practices

✅ **DO:**
- Use Modal for batch processing (scraper)
- Use Modal for bursty workloads (embedding)
- Keep agent service always-on (Render)
- Monitor Modal costs in dashboard
- Set up Modal secrets for API keys

❌ **DON'T:**
- Put user-facing APIs on Modal (cold start issue)
- Use Modal for real-time requirements (<100ms)
- Store persistent data on Modal (use Supabase)
- Run database on serverless

---

## Summary

**Optimal Architecture:**
- **Modal:** Embedding Service + Scraper (68% cost savings)
- **Render:** Agent API (always-on, low latency)
- **Vercel:** Frontend (edge CDN, free tier)
- **Supabase:** Database (managed, free tier)

**Total Cost:** ~$40/month vs $125/month traditional hosting

**Next Steps:**
1. Deploy to Modal: `./backend/scripts/deploy_modal.sh --all`
2. Update .env.prod with Modal URLs
3. Deploy agent to Render
4. Deploy frontend to Vercel
5. Monitor costs and performance

🎉 **Ready for serverless deployment!**
