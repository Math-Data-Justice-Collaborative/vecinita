# Supabase Edge Function Deployment Guide

This guide shows you how to deploy the `search-similar-documents` edge function used by `db_search` retrieval.

## Why Use Edge Functions for Retrieval?

**Benefits:**
- ✅ **Single retrieval contract** for agent runtime
- ✅ **Stable schema boundary** independent of PostgREST profile constraints
- ✅ **Centralized retrieval logic** and easier diagnostics
- ✅ **Auto-scaling** - Supabase handles traffic spikes
- ✅ **No cold starts in agent** - model always warm in edge function

**Tradeoffs:**
- ⚠️ Adds **network roundtrip latency** per retrieval request
- ⚠️ Requires edge function deployment + runtime env wiring

## Prerequisites

### 1. Install Supabase CLI

**Windows (Recommended - Scoop):**
```powershell
# First install Scoop (one-time setup)
powershell -ExecutionPolicy Bypass -Command "irm get.scoop.sh | iex"

# Add Supabase bucket and install
scoop bucket add supabase https://github.com/supabase/scoop-bucket.git
scoop install supabase

# Verify
supabase --version
```

**Alternative (Direct Binary Download):**
Download from: https://github.com/supabase/cli/releases

**Note:** Installing via `npm install -g supabase` is no longer supported. Use Scoop or download binary instead.

### 2. Get HuggingFace Token

1. Go to: https://huggingface.co/settings/tokens
2. Create a new token (Read access is sufficient)
3. Copy the token (starts with `hf_...`)

### 3. Login to Supabase

```bash
supabase login
```

## Deployment

### Option 1: PowerShell Script (Recommended for Windows)

```powershell
# Deploy to production
cd backend/scripts
.\deploy_edge_function.ps1

# Test locally
.\deploy_edge_function.ps1 -Local

# Test production deployment
.\deploy_edge_function.ps1 -Test
```

### Option 2: Manual Deployment

```bash
# From repository root
cd c:\Users\bigme\OneDrive\Documents\GitHub\VECINA\vecinita

# Link to your Supabase project (first time only)
supabase link --project-ref <your-project-ref>

# Deploy the function
supabase functions deploy search-similar-documents
```

**Get your project ref from:**
https://app.supabase.com/project/_/settings/general

## Configuration

### 1. Enable Retrieval Edge Function in Agent Service

**For Render Deployment:**
1. Go to Render Dashboard → vecinita-agent → Environment
2. Add environment variable:
   - Key: `DB_SEARCH_EDGE_FUNCTION`
   - Value: `search-similar-documents`
3. Save and redeploy

**For Docker/Local:**
Add to `.env`:
```bash
DB_SEARCH_EDGE_FUNCTION=search-similar-documents
```

## Testing

### Test Edge Function Directly

```bash
# Using curl (with your actual URL and key)
curl -i https://your-project.supabase.co/functions/v1/search-similar-documents \
  -H "Authorization: Bearer YOUR_SUPABASE_KEY" \
   -H "apikey: YOUR_SUPABASE_KEY" \
  -H "Content-Type: application/json" \
   -d '{"query":"housing support","query_embedding":[0.01,0.02,0.03],"match_threshold":0.1,"match_count":1,"tag_filter":["housing"],"tag_match_mode":"any","include_untagged_fallback":true}'
```

### Test via Agent

```bash
# Start agent locally
cd backend
uv run uvicorn src.agent.main:app --reload

# Test endpoint
curl "http://localhost:8000/ask?question=community+resources"
```

Check logs for:
```
DB Search: RPC call completed. Result type: <class '_EdgeResponse'>
```

## Monitoring

### View Edge Function Logs

**Dashboard:**
https://app.supabase.com/project/_/functions/search-similar-documents/logs

**CLI:**
```bash
supabase functions logs search-similar-documents
```

### Performance Metrics

Expected latencies:
- **Cold start**: 1-2 seconds (first call after inactivity)
- **Warm**: depends on DB load and result size

## Rollback / Fallback

To disable edge retrieval temporarily, unset `DB_SEARCH_EDGE_FUNCTION` and redeploy runtime with your fallback strategy.

## Troubleshooting

### Error: "supabase: command not found"
- Install Supabase CLI: `npm install -g supabase`
- Or download from: https://github.com/supabase/cli/releases

### Error: "404 Not Found" on function URL
- Verify deployment: `supabase functions list`
- Ensure function name is `search-similar-documents`

### Error: "Edge function returned 500"
- View logs: `supabase functions logs generate-embedding`
- Check HuggingFace API status: https://status.huggingface.co/

### Slow responses (>2 seconds)
- First call may have cold start (~1-2s)
- Validate DB RPC and index performance

### Agent retrieval returns empty results
- Check Supabase project URL is correct
- Verify edge function is deployed: `supabase functions list`
- Test edge function directly (see Testing section)

## Next Steps

1. ✅ Deploy edge function
2. ✅ Set DB_SEARCH edge env in runtime
3. ✅ Ensure `search_similar_documents` RPC exists and matches expected signature
4. ✅ Test with sample queries
5. ✅ Monitor performance and adjust as needed
6. 🚀 Continue mirror import cleanup to canonical `src/*`
