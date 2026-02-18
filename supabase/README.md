# Local Supabase Test Environment

This folder contains the configuration for a **local test Supabase instance** running via Docker.

## ⚠️ Important - Production vs Test

- **Production**: Uses cloud Supabase (`https://dosbzlhijkeircyainwz.supabase.co`)
  - Credentials in root `.env` file (never commit!)
  - Used for production deployments
  
- **Test/Local**: Uses this local Docker setup
  - Runs PostgreSQL + PostgREST locally
  - Safe for development and testing
  - No production data access

## Quick Start

```bash
# Start local test Supabase:
cd supabase
docker-compose up -d

# Initialize schema:
./init-local-db.sh

# Stop test environment:
docker-compose down
```

## Environment Configuration

When running tests or local development:
1. Use `config.toml` for Supabase settings
2. Local PostgREST available at: `http://localhost:3001`
3. Local PostgreSQL: `postgresql://postgres:postgres@localhost:5432/postgres`

## Files

- `docker-compose.yml` - Local Supabase services (PostgreSQL, PostgREST, pgAdmin)
- `init-local-db.sql` - Database schema for testing
- `config.toml` - Supabase local configuration
- `.env.test` - Test environment variables (safe to commit with dummy values)

## Production Safety

✅ Production credentials are in **root `.env`** (gitignored)  
✅ This folder contains **only test configurations**  
✅ Local setup **never touches production data**  
