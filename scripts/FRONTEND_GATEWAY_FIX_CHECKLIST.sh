#!/usr/bin/env bash

# VECINITA FRONTEND GATEWAY FIX - QUICK CHECKLIST
# Execute this checklist to restore frontend-to-gateway connectivity
# Error: "Failed to fetch the Gateway is connected to the frontend and agent"

cat << 'EOF'

╔═════════════════════════════════════════════════════════════════════════════╗
║                      VECINITA FRONTEND GATEWAY FIX                          ║
║                                                                             ║
║  Error: "Failed to fetch" when frontend tries to reach gateway              ║
║  Fix: Set VITE_GATEWAY_URL to deployed gateway URL in Render               ║
║                                                                             ║
║  Estimated time: 10 minutes                                                ║
║  Difficulty: Easy                                                          ║
╚═════════════════════════════════════════════════════════════════════════════╝

PHASE 1: Update Frontend Environment Variables
═════════════════════════════════════════════════════════════════════════════

[ ] Step 1.1: Open Render Dashboard
    URL: https://dashboard.render.com
    
[ ] Step 1.2: Navigate to Frontend Service
    Service Name: vecinita-frontend
    
[ ] Step 1.3: Go to Environment section
    Click: Service Settings → Environment
    
[ ] Step 1.4: Add/Update VITE_GATEWAY_URL
    Variable Name:  VITE_GATEWAY_URL
    Variable Value: https://vecinita-gateway-prod-v5.onrender.com/api/v1
    Click: Save
    
    ⚠️  CRITICAL: Without this, frontend defaults to http://localhost:8004
                 which doesn't exist in production!
    
[ ] Step 1.5: Verify other environment variables
    Optional but recommended:
    - VITE_AGENT_REQUEST_TIMEOUT_MS=90000
    - VITE_AGENT_STREAM_TIMEOUT_MS=120000
    - VITE_ADMIN_AUTH_ENABLED=true

PHASE 2: Verify Gateway Configuration
═════════════════════════════════════════════════════════════════════════════

[ ] Step 2.1: Open Gateway Service Settings
    Service Name: vecinita-gateway-prod-v5
    Section: Environment
    
[ ] Step 2.2: Check AGENT_URL
    Expected Value: https://vecinita-agent.onrender.com
    If missing: Add and save
    
[ ] Step 2.3: Check CORS_ORIGINS
    Expected Value: https://vecinita-frontend.onrender.com (minimum)
    If missing: Add and save
    
[ ] Step 2.4: Restart Gateway (if you made changes)
    Click: Service → More → Restart

PHASE 3: Trigger Frontend Redeploy
═════════════════════════════════════════════════════════════════════════════

Choose ONE of these methods:

Option A: Render Dashboard (Easiest)
  [ ] Step 3A.1: Open vecinita-frontend service
  [ ] Step 3A.2: Click "Deploy" button (top right)
  [ ] Step 3A.3: Select "Redeploy Latest Commit"
  [ ] Step 3A.4: Wait for build to complete (~3-5 minutes)

Option B: GitHub CLI (Recommended for automation)
  [ ] Step 3B.1: Run command:
     
     gh workflow run deploy.yml \
       --repo joseph-c-mcguire/Vecinitafrontend \
       --ref main
     
  [ ] Step 3B.2: Monitor status:
     
     gh run list --repo joseph-c-mcguire/Vecinitafrontend \
       --workflow deploy.yml -L 1

Option C: Git Push (Automatic trigger)
  [ ] Step 3C.1: Run commands:
     
     git add frontends/chat/.env.production
     git commit -m "fix: Configure gateway URL for production"
     git push origin main
  
  [ ] Step 3C.2: GitHub Actions will automatically trigger deploy

PHASE 4: Verification & Testing
═════════════════════════════════════════════════════════════════════════════

Wait for deployment to complete (status: "Live" in Render Dashboard)

[ ] Step 4.1: Service Health Checks
    Run these curl commands:
    
    curl -I https://vecinita-frontend.onrender.com
      → Should return 200 OK
    
    curl https://vecinita-gateway-prod-v5.onrender.com/health
      → Should return health response
    
    curl https://vecinita-agent.onrender.com/health
      → Should return health response

[ ] Step 4.2: Browser Test (Best Validation)
    1. Open: https://vecinita-frontend.onrender.com
    2. Press F12 to open Developer Console
    3. Go to Network tab
    4. Type a question in the chat input
    5. Click "Send" or press Enter
    6. Look for POST request to /api/v1/ask
       ✓ Status 200 or 201 = SUCCESS ✓
       ✗ Status 404           = Gateway URL not configured
       ✗ CORS error           = Check gateway CORS_ORIGINS
       ✗ Failed to fetch      = Network unreachable

[ ] Step 4.3: Console Check
    In DevTools Console tab, look for:
    ✓ No "Failed to fetch" errors
    ✓ No "CORS policy" errors  
    ✓ No network timeouts

TROUBLESHOOTING
═════════════════════════════════════════════════════════════════════════════

If you see "Failed to fetch":

  Problem: Deployment hasn't finished yet
  Solution: Wait 5 more minutes and refresh browser
            Check Render Dashboard → Deploys tab for status
  
  Problem: Environment variable not saved
  Solution: Go to Render Dashboard → vecinita-frontend → Environment
            Verify VITE_GATEWAY_URL is present and correct
            If not there, add it and click Save again
  
  Problem: Browser cached old version
  Solution: Press Ctrl+Shift+Delete (Windows) or Cmd+Shift+Delete (Mac)
            Clear all cache and cookies
            Reload page
  
  Problem: Gateway service is down
  Solution: Check Render Dashboard → vecinita-gateway-prod-v5
            If status says "Failed" or "Error", click Restart

EXPECTED OUTCOME
═════════════════════════════════════════════════════════════════════════════

After completing all checks, you should see:

  ✓ Frontend loads successfully at https://vecinita-frontend.onrender.com
  ✓ Chat input field is functional
  ✓ Network requests to /api/v1/ask return 200 status
  ✓ Messages are sent and received from gateway → agent → LLM
  ✓ No "Failed to fetch" errors in console

REFERENCE INFORMATION
═════════════════════════════════════════════════════════════════════════════

Critical Service URLs:
  - Frontend URL:    https://vecinita-frontend.onrender.com
  - Gateway URL:     https://vecinita-gateway-prod-v5.onrender.com
  - Agent URL:       https://vecinita-agent.onrender.com
  - Database URL:    postgresql://...@dpg-d6or4g2a214c73f6hl20-a.virginia-postgres.render.com

Key Variable to Set (MOST IMPORTANT):
  VITE_GATEWAY_URL=https://vecinita-gateway-prod-v5.onrender.com/api/v1

For More Information:
  See: docs/FRONTEND_GATEWAY_FIX.md

═════════════════════════════════════════════════════════════════════════════

EOF

echo ""
echo "Use this checklist as you fix the frontend-gateway connectivity issue."
echo "Open the URL steps at: https://dashboard.render.com"
echo ""
