# 🔐 Security & Environment Configuration Guide

## ⚠️ CRITICAL: Production Secrets

### What Gets Committed (Safe)
✅ `supabase/.env.test` - Template with dummy values  
✅ `backend/.env.test` - Template with dummy values  
✅ `backend/.env.example` - Template documentation  
✅ All `.sh` scripts in `supabase/`  

### What NEVER Gets Committed (Secrets)
❌ `.env` (root) - **PRODUCTION CREDENTIALS**  
❌ `backend/.env` - **PRODUCTION CREDENTIALS**  
❌ `supabase/.env` - Local secrets (if created)  
❌ Any file with real API keys  

## Production vs Test Environments

### Production (Cloud Supabase)
**Location:** Root `.env` file  
**Supabase URL:** `https://dosbzlhijkeircyainwz.supabase.co`  
**Database:** `db.dosbzlhijkeircyainwz.supabase.co:5432`  
**Usage:** Production deployments only  
**Safety:** ✅ Gitignored by default  

### Test/Local (Docker Supabase)
**Location:** `supabase/` folder  
**Supabase URL:** `http://localhost:3001`  
**Database:** `localhost:54321`  
**Usage:** Local development and testing  
**Safety:** ✅ Uses separate test credentials  

## Environment Setup

### For Production Deployment
```bash
# Use root .env file (already configured)
# Contains real Supabase credentials
# NEVER commit this file!

# Verify .gitignore includes .env
grep "^\.env$" .gitignore
```

### For Local Testing
```bash
# Start local test Supabase
cd supabase
./start-local.sh

# Copy test config to backend
cp backend/.env.test backend/.env

# Add your real API keys for testing:
# Edit backend/.env and add:
#   DEEPSEEK_API_KEY=sk-...
#   GROQ_API_KEY=gsk-...
#   etc.
```

## Quick Start Workflows

### Switch to Test Environment
```bash
# 1. Start local Supabase
cd supabase && ./start-local.sh

# 2. Configure backend for local testing
cp backend/.env.test backend/.env
# Edit backend/.env to add your API keys

# 3. Run backend locally
cd backend
uv run uvicorn src.agent.main:app --reload
```

### Switch to Production Environment
```bash
# 1. Restore production config
# (Root .env already has production credentials)

# 2. Run backend with production Supabase
cd backend
uv run uvicorn src.agent.main:app --reload
```

## Security Checklist

Before committing:
- [ ] Verify `.env` is in `.gitignore`
- [ ] Check no API keys in committed files: `git diff --cached | grep -i api_key`
- [ ] Ensure only test templates committed
- [ ] Production credentials stay in gitignored files

## Files Reference

```
.
├── .env                          ❌ NEVER COMMIT (Production secrets)
├── .gitignore                    ✅ Includes .env
├── backend/
│   ├── .env                      ❌ NEVER COMMIT (Active config)
│   ├── .env.example              ✅ Safe template
│   └── .env.test                 ✅ Safe test template
└── supabase/
    ├── .env.test                 ✅ Safe test template
    ├── docker-compose.yml        ✅ Test infrastructure
    ├── start-local.sh            ✅ Test startup script
    ├── init-local-db.sh          ✅ Schema initialization
    ├── test-connection.sh        ✅ Verification script
    └── README.md                 ✅ Documentation
```

## Troubleshooting

### "I accidentally committed .env!"
```bash
# Remove from git history (use with caution!)
git rm --cached .env
git rm --cached backend/.env

# Add to .gitignore if not already there
echo ".env" >> .gitignore
echo "backend/.env" >> .gitignore

# Commit the removal
git commit -m "Remove sensitive .env files from tracking"

# ⚠️ IMPORTANT: Rotate all exposed API keys!
```

### "Which environment am I using?"
```bash
# Check backend configuration
grep SUPABASE_URL backend/.env

# If shows localhost:3001 → Test environment
# If shows dosbzlhijkeircyainwz.supabase.co → Production
```

## Getting Help

- **Local test setup:** See `supabase/README.md`
- **Production deployment:** See root `.env` (never commit!)
- **Security concerns:** Contact repository owner
