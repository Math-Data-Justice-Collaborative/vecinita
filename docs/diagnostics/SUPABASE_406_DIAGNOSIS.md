# Supabase 406/404 Error - Diagnosis & Fix

**Date:** February 8, 2026  
**Status:** ✅ DIAGNOSED - Schema Missing in Production

## Problem Summary

Backend receiving HTTP 406 "Not Acceptable" (now showing as 404) errors when accessing Supabase.

## Root Cause

1. **Production Supabase Missing Schema**
   - Table `document_chunks` doesn't exist in production database
   - RPC function `search_similar_documents` not created
   - Error: `PGRST205` - "relation does not exist"

2. **Configuration Mismatch**
   - `backend/.env` points to **production Supabase**: `https://dosbzlhijkeircyainwz.supabase.co`
   - `docker-compose.yml` gateway/auth services point to **local PostgREST**: `http://postgrest:3000`
   - Agent service uses production (from .env), others use local

## Verification

```bash
# Direct API test confirmed:
curl "https://dosbzlhijkeircyainwz.supabase.co/rest/v1/document_chunks?select=id&limit=1" \
  -H "apikey: <key>" -H "Authorization: Bearer <key>"

# Response:
HTTP/2 404
proxy-status: PostgREST; error=PGRST205
# Translation: Table doesn't exist
```

## Solutions

### Option 1: Local Development (Recommended for Testing)

**Use local PostgreSQL + PostgREST instead of production Supabase**

#### Step 1: Update backend/.env for local development
```bash
# Change from:
SUPABASE_URL=https://dosbzlhijkeircyainwz.supabase.co
SUPABASE_KEY=eyJhbGci...

# To:
SUPABASE_URL=http://localhost:3001  # Local PostgREST
SUPABASE_KEY=dev-anon-key           # Local dev key
```

#### Step 2: Initialize local database schema
```bash
# Start services
docker-compose up -d postgres postgrest

# Wait for postgres to be ready
sleep 10

# Run schema installation
docker-compose exec postgres psql -U postgres -d postgres -f /path/to/schema_install.sql
# OR if schema_install.sql is in backend/scripts/:
docker-compose exec postgres psql -U postgres -d postgres < backend/scripts/schema_install.sql
```

#### Step 3: Restart services
```bash
docker-compose down
docker-compose up -d
```

### Option 2: Setup Production Supabase (For Production Use)

**Create schema in your production Supabase database**

#### Step 1: Connect to Supabase SQL Editor
1. Go to: https://supabase.com/dashboard/project/dosbzlhijkeircyainwz
2. Navigate to: SQL Editor

#### Step 2: Run schema installation
```sql
-- Run the contents of backend/scripts/schema_install.sql
-- This creates:
-- 1. document_chunks table
-- 2. embedding column with vector type
-- 3. search_similar_documents RPC function
-- 4. Indexes for performance
```

#### Step 3: Verify schema
```sql
-- Check table exists
SELECT * FROM document_chunks LIMIT 1;

-- Check RPC function exists
SELECT search_similar_documents(
    ARRAY[0.0, 0.0, 0.0]::vector(384),
    0.0,
    1
);
```

## Configuration Matrix

| Environment | SUPABASE_URL | SUPABASE_KEY | Use Case |
|-------------|--------------|--------------|----------|
| **Local Dev** | `http://localhost:3001` | `dev-anon-key` | Testing with docker-compose |
| **Production** | `https://dosbzlhijkeircyainwz.supabase.co` | `eyJhbGci...` | Live deployment |

## Recommended Action

For **local development/testing**:
1. ✅ Use Option 1 (local PostgREST)
2. ✅ Initialize schema in local database
3. ✅ Keep production credentials in separate `.env.prod` file

For **production deployment**:
1. ✅ Use Option 2 (production Supabase)
2. ✅ Run schema_install.sql in Supabase SQL Editor
3. ✅ Verify tables and RPC functions exist

## Files to Update

### For Local Development:
- `backend/.env` - Change SUPABASE_URL to local PostgREST
- Verify `docker-compose.yml` PostgreSQL is running
- Run schema installation script

### For Production:
- Keep `backend/.env` with production URL
- Run schema in Supabase dashboard
- Deploy to production environment (not local Docker)
