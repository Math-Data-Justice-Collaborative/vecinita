# Supabase Configuration for Vecinita Chat & Data Management

> Status (March 2026): Supabase is now scoped primarily to authentication and related role/session metadata. Vector/document retrieval and ingestion are being migrated to Render Postgres.

For the full cross-service integration map (frontend, gateway, agent, direct-routing, scraper, databases, auth boundaries), see [docs/architecture/SERVICE_INTEGRATION_POINTS.md](docs/architecture/SERVICE_INTEGRATION_POINTS.md).

## Overview

Both the **Chat Application** and **Data Management System** use the same Supabase instance for:
- Authentication (JWT tokens)
- Role/session metadata used by auth and admin flows
- File storage (documents bucket)

Vector data backend target:
- Render Postgres (`DATABASE_URL`) is the canonical backend for vector retrieval/write paths.
- Agent services should set `DB_DATA_MODE=postgres` and `VECTOR_SYNC_SUPABASE_FALLBACK_READS=false` for production cutover.

## Supabase Instance Details

```
Project URL: https://your-project.supabase.co
Region: us-east-2
Database: PostgreSQL 16
```

## Configuration Keys

### Authentication Layer

| Key | Value | Used By | Purpose |
|-----|-------|---------|---------|
| `SUPABASE_URL` | `https://your-project.supabase.co` | Both frontends, both backends | Base project URL |
| `SUPABASE_KEY` | `<supabase-service-role-key>` | Both backends | Service role key (private) |
| `SUPABASE_PUBLISHABLE_KEY` | `<supabase-anon-key>` | Both frontends | Public anon key for UI |
| `SUPABASE_SECRET_KEY` | `<supabase-service-role-key>` | Both backends | Service role (same as SUPABASE_KEY) |
| `SUPABASE_PERSONAL_ACCESS_TOKEN` | `<supabase-personal-access-token>` | Migrations, admin tasks | Admin token |

### Frontend-Specific Keys

| Key | Value | Used By | Purpose |
|-----|-------|---------|---------|
| `VITE_SUPABASE_URL` | `https://your-project.supabase.co` | Chat Frontend, DM Frontend | Exposed to browser |
| `VITE_SUPABASE_ANON_KEY` | `<supabase-anon-key>` | Chat Frontend, DM Frontend | Safe for browser (anon key) |

### Database Connection

| Key | Value | Used By | Purpose |
|-----|-------|---------|---------|
| `DATABASE_URL` | `postgresql://postgres.your-project-ref:<db-password>@aws-<region>.pooler.supabase.com:5432/postgres?sslmode=require` | Chat Agent, Gateway, DM API | Connection pooling |
| `DB_HOST` | `aws-<region>.pooler.supabase.com` | Scraper, CLI tools | Direct host |
| `DB_PORT` | `5432` | All database clients | Postgres port |
| `DB_USER` | `postgres.your-project-ref` | All database clients | Pooled connection user |
| `DB_PASSWORD` | `<db-password>` | All database clients | Pooled connection password |
| `DB_NAME` | `postgres` | All database clients | Default database |

## How Each System Uses Supabase

### Chat Frontend

```typescript
// frontend/src/main.ts
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(
  import.meta.env.VITE_SUPABASE_URL,      // https://...supabase.co
  import.meta.env.VITE_SUPABASE_ANON_KEY  // sb_public_...
)

// User authentication
const { data, error } = await supabase.auth.signInWithPassword({
  email: user.email,
  password: user.password
})
```

### Chat Backend (Gateway)

```python
# backend/src/api/main.py
from supabase import create_client

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")  # Service role (full access)
)

# Query database
response = supabase.table("documents").select("*").execute()

# Vector search via edge function
response = supabase.functions.invoke(
    "search-similar-documents",
    invoke_options={
        "body": {"query_embedding": embedding, "match_count": 5}
    }
)
```

### Chat Backend (Agent)

```python
# backend/src/agent/main.py
from supabase import create_client

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

# Vector search for RAG
def search_documents(query_embedding):
    response = supabase.from_("documents").select("*") \
        .order("similarity(embedding, %s)", desc=True) \
        .limit(5) \
        .execute()
    return response.data
```

### Data Management Frontend

```typescript
// apps/data-management-frontend/src/main.ts
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(
  import.meta.env.VITE_SUPABASE_URL,      // Same as Chat Frontend
  import.meta.env.VITE_SUPABASE_ANON_KEY  // Same as Chat Frontend
)

// Can share auth session with Chat frontend
const { data: { session } } = await supabase.auth.getSession()
```

### Data Management API

```python
# services/data-management-api/apps/backend/main.py
from supabase import create_client

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SECRET_KEY")  # Service role
)

# Manage documents/data
documents = supabase.table("documents").select("*").execute()
```

## Shared Resources

Both Chat and Data Management systems access:

### Tables

| Table | Created By | Used By | Purpose |
|-------|-----------|---------|---------|
| `auth.users` | Supabase | Both frontends | User accounts |
| `documents` | Scraper / DM API | Chat Agent, DM API | Document storage |
| `document_chunks` | Scraper | Chat Agent | Vector search source |
| `sessions` | Both backends | Both backends | RAG context cache |
| `search_logs` | Chat Agent | Monitoring | Query logging |

### Storage Buckets

| Bucket | Used By | Purpose |
|--------|---------|---------|
| `documents` | DM API, Agent | Document file storage |
| `scraper-uploads` | Scraper | Scraper artifacts |

### Edge Functions

| Function | Called By | Purpose |
|----------|-----------|---------|
| `search-similar-documents` | Chat Gateway | Vector similarity search |
| `reindex-documents` | Scraper, Chat Agent | Rebuild vector index |

## Environment Variable Sourcing

### Local Development (Root `.env`)

```bash
# Root .env (shared by all)
SUPABASE_URL=https://...
SUPABASE_KEY=<supabase-service-role-key>
VITE_SUPABASE_URL=https://...
VITE_SUPABASE_ANON_KEY=<supabase-anon-key>
DATABASE_URL=postgresql://...
```

When you run `make dev-chat` or `make dev-data-management`, both systems source from the same root `.env`:

```bash
make dev-chat              # Chat sources root .env
make dev-data-management   # DM sources root .env
# Both see the same SUPABASE_URL and can access shared data
```

### Render Deployment

Supabase credentials are set in Render dashboard (not committed to repo):

```yaml
# render.yaml
services:
  - name: vecinita-chat-frontend
    envVars:
      - key: VITE_SUPABASE_URL
        sync: false  # Set manually in Render dashboard
      - key: VITE_SUPABASE_ANON_KEY
        sync: false
        
  - name: vecinita-chat-backend
    envVars:
      - key: SUPABASE_URL
        sync: false
      - key: SUPABASE_KEY
        sync: false
      - key: DATABASE_URL
        sync: false
```

## Testing Supabase Connection

### Chat Frontend
```bash
# In browser console
const { data, error } = await supabase.auth.getSession()
console.log(data?.session?.user?.email)  # Should show logged-in user
```

### Chat Backend
```bash
# In backend container
curl -H "Authorization: Bearer $SUPABASE_SECRET_KEY" \
  "$SUPABASE_URL/rest/v1/documents" \
  -H "apikey: $SUPABASE_PUBLISHABLE_KEY"
```

### Data Management
```bash
# Same as Chat Backend - uses same Supabase credentials
```

## Troubleshooting

### "401 Unauthorized" in Frontend
**Problem:** Frontend can't authenticate\
**Check:**
1. `VITE_SUPABASE_ANON_KEY` is set correctly
2. Supabase RLS (Row Level Security) policies allow anonymous access
3. Try: `curl -H "apikey: $VITE_SUPABASE_ANON_KEY" https://...supabase.co/rest/v1/documents`

### "403 Forbidden" in Backend  
**Problem:** Backend can't write to database\
**Check:**
1. `SUPABASE_KEY` is the SERVICE ROLE key (not anon key)
2. RLS policies allow service role access
3. Try: `curl -H "Authorization: Bearer $SUPABASE_KEY" https://...supabase.co/rest/v1/documents`

### Both Systems See Different Data
**Problem:** Chat and DM viewing different databases\
**Check:**
1. Both source from root `.env` ✓
2. `SUPABASE_URL` is identical in both ✓
3. Run: `make dev-chat` in one terminal, verify Chat agent logs show Supabase URL
4. Run: `make dev-data-management` in another terminal, verify DM API logs show SAME URL

### Vector Search Not Working
**Problem:** Edge function returns 404\
**Check:**
1. Edge function `search-similar-documents` exists in Supabase
2. Embedding dimensions match (384 for all-MiniLM-L6-v2)
3. Check: `supabase functions list` (requires CLI)

## Key Security Notes

⚠️ **DO NOT commit real `.env` to Git**
- `SUPABASE_KEY` (service role) has full database access
- `SUPABASE_SECRET_KEY` same as above - admin-level
- `DATABASE_URL` includes plaintext password

✅ **Safe to expose:**
- `VITE_SUPABASE_URL` - Supabase allows public access to projects
- `VITE_SUPABASE_ANON_KEY` - Limited by RLS policies

## References

- [Supabase JavaScript Client](https://supabase.com/docs/reference/javascript/introduction)
- [Supabase Python Client](https://supabase.com/docs/reference/python/introduction)
- [Row Level Security Setup](https://supabase.com/docs/guides/auth/row-level-security)
- [Edge Functions](https://supabase.com/docs/guides/functions)
