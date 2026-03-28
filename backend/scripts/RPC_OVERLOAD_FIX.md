# RPC Overload Fix

## Problem
You're seeing this error:
```
Could not choose the best candidate function between: 
public.search_similar_documents(query_embedding => public.vector, match_threshold => double precision, match_count => integer), 
public.search_similar_documents(query_embedding => public.vector, match_threshold => real, match_count => integer)
```

**Root Cause**: The database has two conflicting versions of the `search_similar_documents` function - one using `REAL` and another using `DOUBLE PRECISION` for the `match_threshold` parameter. PostgREST (Supabase's API layer) cannot determine which one to call.

## Quick Fix

### Option 1: Run SQL Script (Recommended)
1. Open your Supabase Dashboard → SQL Editor
2. Copy and paste the contents of [`fix_rpc_overload.sql`](fix_rpc_overload.sql)
3. Click "Run"
4. Restart your backend server

### Option 2: Manual Commands
Run these commands in Supabase SQL Editor:

```sql
-- Drop all versions
DROP FUNCTION IF EXISTS search_similar_documents(vector, DOUBLE PRECISION, INTEGER);
DROP FUNCTION IF EXISTS search_similar_documents(vector, REAL, INTEGER);

-- Recreate with REAL type (canonical version)
CREATE OR REPLACE FUNCTION search_similar_documents(
    query_embedding vector,
    match_threshold REAL DEFAULT 0.3,
    match_count INTEGER DEFAULT 5
)
RETURNS TABLE (
    id UUID,
    content TEXT,
    source_url TEXT,
    chunk_index INTEGER,
    metadata JSONB,
    similarity DOUBLE PRECISION
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        dc.id,
        dc.content,
        dc.source_url,
        dc.chunk_index,
        dc.metadata,
        1 - (dc.embedding <=> query_embedding) AS similarity
    FROM document_chunks dc
    WHERE dc.embedding IS NOT NULL
        AND dc.is_processed = TRUE
        AND 1 - (dc.embedding <=> query_embedding) > match_threshold
    ORDER BY dc.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;
```

## Verification

After running the fix, verify only one version exists:

```sql
SELECT 
    routine_name,
    parameter_name,
    udt_name
FROM information_schema.parameters
WHERE specific_schema = 'public'
    AND routine_name = 'search_similar_documents'
ORDER BY ordinal_position;
```

Expected output:
```
routine_name              | parameter_name  | udt_name
--------------------------+-----------------+----------
search_similar_documents  | query_embedding | vector
search_similar_documents  | match_threshold | float4
search_similar_documents  | match_count     | int4
```

## Why This Happened

This typically occurs when:
1. Running `schema_install.sql` multiple times with different parameter types
2. Running both `update_rpc.py` and `update_rpc_psycopg.py` (which may use different types)
3. Manual schema modifications that created duplicate functions

## Prevention

- Use only `schema_install.sql` for initial setup (uses REAL)
- Don't run both `update_rpc*.py` scripts unless you know they're compatible
- Always check existing functions before creating new ones with the same name

## Related Files

- [`schema_install.sql`](schema_install.sql) - Main schema with canonical function definition (line 179)
- [`fix_rpc_overload.sql`](fix_rpc_overload.sql) - This fix script
- [`db_search.py`](../src/agent/tools/db_search.py) - Updated with error detection for PGRST203
