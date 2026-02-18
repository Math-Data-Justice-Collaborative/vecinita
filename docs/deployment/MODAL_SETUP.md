╔════════════════════════════════════════════════════════════════╗
║           🚀 MODAL SERVERLESS DEPLOYMENT GUIDE                 ║
╚════════════════════════════════════════════════════════════════╝

WHY USE MODAL?
═══════════════════════════════════════════════════════════════════

✅ Cost Savings: 68% cheaper ($40/month vs $125/month)
✅ Auto-Scaling: Scales to zero when idle, scales up on demand
✅ Perfect For: Embedding service (bursty) and scraper (scheduled)
✅ Zero DevOps: No servers to manage


DEPLOYMENT ARCHITECTURE
═══════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────┐
│ PRODUCTION SETUP                                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Frontend (Vercel)          FREE                            │
│      ↓                                                      │
│  Agent API (Render)         $25/month (always-on)          │
│      ↓                                                      │
│  Embedding (Modal)          $10/month (serverless)         │
│  Scraper (Modal)            $5/month (scheduled)           │
│      ↓                                                      │
│  Database (Supabase)        FREE                            │
│                                                             │
│  TOTAL: ~$40/month                                          │
└─────────────────────────────────────────────────────────────┘


QUICK START - DEPLOY TO MODAL
═══════════════════════════════════════════════════════════════════

1. Install Modal CLI:
   $ pip install modal

2. Authenticate:
   $ modal token new
   (Opens browser, follow prompts)

3. Deploy services:
   $ ./backend/scripts/deploy_modal.sh --all

4. Save the URLs shown (e.g., https://your--vecinita-embedding-web.modal.run)

5. Update production environment:
   $ nano .env.prod
   
   Add these lines:
   EMBEDDING_SERVICE_URL=https://your-modal-url.modal.run
   SCRAPER_SERVICE_URL=https://your-modal-url.modal.run

6. Deploy agent to Render with updated .env.prod


WHAT RUNS WHERE?
═══════════════════════════════════════════════════════════════════

LOCAL DEVELOPMENT (docker-compose):
  • All services run in Docker containers
  • Embedding: http://localhost:8001
  • Scraper: http://localhost:8002
  • Agent: http://localhost:8000

PRODUCTION:
  • Embedding → Modal (serverless, auto-scales)
  • Scraper → Modal (cron-scheduled)
  • Agent → Render (always-on)
  • Frontend → Vercel (edge CDN)
  • Database → Supabase (managed)


MONITORING & MANAGEMENT
═══════════════════════════════════════════════════════════════════

View Modal Apps:
  $ modal app list

View Logs:
  $ modal app logs vecinita-embedding
  $ modal app logs vecinita-scraper

Update/Redeploy:
  $ ./backend/scripts/deploy_modal.sh --embedding --force
  $ ./backend/scripts/deploy_modal.sh --scraper --force

Check Costs:
  → https://modal.com/dashboard (view usage and costs)


COST BREAKDOWN
═══════════════════════════════════════════════════════════════════

Traditional (All on Render):
  Agent:     $25/month
  Embedding: $50/month (2GB RAM, always-on)
  Scraper:   $50/month (2GB RAM, always-on)
  ────────────────────
  TOTAL:     $125/month

Hybrid (Modal + Render):
  Agent:     $25/month (Render)
  Embedding: $10/month (Modal, pay-per-use)
  Scraper:   $5/month  (Modal, scheduled runs)
  ────────────────────
  TOTAL:     $40/month

SAVINGS: 68% ($85/month)


WHY THIS ARCHITECTURE?
═══════════════════════════════════════════════════════════════════

Embedding Service → Modal ✅
  • Loads 200MB ML model
  • Bursty traffic (not always needed)
  • Can tolerate 3-5s cold start
  • Auto-scales during high demand

Scraper Service → Modal ✅
  • Runs on schedule (e.g., daily at 2 AM)
  • Idle 95% of the time
  • Resource-intensive during runs
  • Perfect for batch processing

Agent API → Render ✅
  • Needs to be always-on
  • Low latency required (<100ms)
  • User-facing, can't have cold starts
  • Frequent access pattern


DEPLOYMENT SEQUENCE
═══════════════════════════════════════════════════════════════════

1. Test locally:
   $ ./setup.sh

2. Deploy Modal services:
   $ ./backend/scripts/deploy_modal.sh --all

3. Update .env.prod with Modal URLs

4. Deploy agent to Render:
   (Push to GitHub or deploy manually)

5. Deploy frontend to Vercel:
   $ cd frontend && vercel deploy --prod


TROUBLESHOOTING
═══════════════════════════════════════════════════════════════════

"Modal service timeout"
  → Check logs: modal app logs vecinita-embedding
  → Verify auth: modal token new

"Embedding service unreachable"
  → Test endpoint: curl https://your-modal-url/health
  → Check Modal dashboard for errors

"High latency on first request"
  → Expected: Modal cold start (3-5 seconds)
  → Solution: Keep-alive ping every 4 minutes


COMPLETE DOCUMENTATION
═══════════════════════════════════════════════════════════════════

Full Guide:    docs/MODAL_HYBRID_ARCHITECTURE.md
Deploy Script: backend/scripts/deploy_modal.sh
Quick Start:   IMPLEMENTATION_SUMMARY.md


═══════════════════════════════════════════════════════════════════

Ready to deploy? Run:
  $ ./backend/scripts/deploy_modal.sh --all

═══════════════════════════════════════════════════════════════════
