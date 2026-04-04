# 🔧 Quick Fix for Supabase 406/404 Error

## TL;DR - Run This Now

```bash
# Quick fix for local development:
./run/setup_local_dev.sh
```

This script will:
✅ Configure backend to use local PostgREST  
✅ Initialize database schema  
✅ Start all Docker services  
✅ Preserve your API keys  

---

## What Was Wrong?

**Problem:** Backend trying to use production Supabase, but `document_chunks` table doesn't exist there.

**Error Logs:**
```
HTTP/2 406 Not Acceptable
HTTP/2 404 Not Found
routing-status: PostgREST; error=PGRST205
```

**Translation:** Table doesn't exist in production database → connection fails.

---

## Solution Options

### Option 1: Local Development (Recommended) ⭐

**Use Case:** Testing, local development with docker-compose

```bash
# Automated setup (recommended):
./run/setup_local_dev.sh

# Manual setup:
# 1. Update backend/.env:
SUPABASE_URL=http://localhost:3001
SUPABASE_KEY=dev-anon-key

# 2. Start services and init schema:
docker-compose up -d postgres postgrest
sleep 10
docker-compose exec -T postgres psql -U postgres -d postgres < backend/scripts/schema_install.sql

# 3. Start all services:
docker-compose up -d
```

**Verify:**
```bash
# Check services:
docker-compose ps

# Test db-info endpoint:
curl http://localhost:8000/db-info
```

### Option 2: Production Supabase

**Use Case:** Production deployment, using cloud Supabase

**Steps:**
1. Go to Supabase Dashboard: https://supabase.com/dashboard/project/dosbzlhijkeircyainwz
2. Navigate to: **SQL Editor**
3. Copy contents of `backend/scripts/schema_install.sql`
4. Run in SQL Editor
5. Verify:
   ```sql
   SELECT * FROM document_chunks LIMIT 1;
   SELECT search_similar_documents(ARRAY[0.0]::vector(384), 0.0, 1);
   ```

---

## Configuration Quick Reference

| Environment | SUPABASE_URL | Database |
|-------------|--------------|----------|
| 🏠 **Local Dev** | `http://localhost:3001` | Docker PostgreSQL |
| ☁️ **Production** | `https://dosbzlhijkeircyainwz.supabase.co` | Cloud Supabase |

---

## Troubleshooting

### "Connection refused" on localhost:3001
```bash
# Start PostgREST:
docker-compose up -d postgrest

# Check status:
docker-compose ps postgrest
```

### "Table doesn't exist" error
```bash
# Reinstall schema:
docker-compose exec -T postgres psql -U postgres -d postgres < backend/scripts/schema_install.sql
```

### Want to switch back to production?
```bash
# Restore backup:
cp backend/.env.backup backend/.env

# Restart services:
docker-compose restart
```

---

## Next Steps

After running `./run/setup_local_dev.sh`:

1. **Test the fix:**
   ```bash
   curl http://localhost:8000/db-info
   # Should return: "status": "success"
   ```

2. **Test a query:**
   ```bash
   curl "http://localhost:8000/ask?question=test&lang=en&provider=deepseek"
   ```

3. **View logs:**
   ```bash
   docker-compose logs -f vecinita-agent
   # Should see: "Supabase client initialized successfully"
   ```

4. **Access services:**
   - Agent API: http://localhost:8000
   - Gateway: http://localhost:8002
   - pgAdmin: http://localhost:5050 (admin@example.com / admin)

---

## Files Created

- ✅ `SUPABASE_406_DIAGNOSIS.md` - Full diagnosis report
- ✅ `run/setup_local_dev.sh` - Automated setup script
- ✅ `QUICK_FIX.md` - This guide

---

Compatibility note: `./setup_local_dev.sh` remains available as a root wrapper shim.

**Ready to proceed?** Run: `./run/setup_local_dev.sh`
