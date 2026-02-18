# DB Search Diagnostic Guide

## Problem: DB Search Returning No Results

You've noticed that `db_search` is returning empty results even though your database has content (e.g., DHS Rhode Island data).

## Quick Diagnosis Steps

### 1. Test the Search Endpoint

**Start the backend:**

```bash
cd backend
uv run -m uvicorn src.agent.main:app --reload
```

**Test with diagnostic endpoint:**

```bash
# Open in browser or use curl
http://localhost:8000/test-db-search?query=community%20resources

# Or with curl
curl "http://localhost:8000/test-db-search?query=rhode%20island"
```

**Expected Response:**

```json
{
  "status": "success",
  "query": "rhode island",
  "embedding_dimension": 384,
  "results_found": 5,
  "similarity_range": {
    "min": 0.123,
    "max": 0.789,
    "avg": 0.456
  },
  "sample_result": {
    "content_preview": "DOCUMENTS_LOADED: 1 | DOCUMENTS_PROCESSED: 1...",
    "source_url": "https://dhs.ri.gov/",
    "similarity": 0.789
  },
  "all_similarities": [0.789, 0.678, 0.567, ...]
}
```

### 2. Check What You Get

#### Scenario A: "no_results" with total_rows_in_table > 0

**Problem:** RPC function exists, data exists, but embeddings don't match

**Solutions:**

1. **Check embedding dimension mismatch**
   - Your data shows embeddings (384 dimensions for sentence-transformers/all-MiniLM-L6-v2)
   - Verify pgvector column is `vector(384)`

2. **Check RPC function signature**

   ```sql
   -- Run in Supabase SQL Editor
   SELECT 
       proname as function_name,
       pg_get_function_arguments(oid) as arguments,
       pg_get_function_result(oid) as result_type
   FROM pg_proc 
   WHERE proname = 'search_similar_documents';
   ```

   Expected: Function should accept `query_embedding vector(384)`

3. **Verify data format**

   ```sql
   -- Check if embeddings are stored correctly
   SELECT 
       id,
       source_url,
       chunk_index,
       array_length(embedding::real[], 1) as embedding_dim
   FROM content_chunks
   LIMIT 5;
   ```

#### Scenario B: "error" with PostgreSQL error

**Problem:** RPC function issue

**Common Errors:**

**PGRST203 - Function Overload:**

```bash
# Run the fix script
psql $DATABASE_URL -f backend/scripts/fix_rpc_overload.sql
```

**Function not found:**

```bash
# Install schema
psql $DATABASE_URL -f backend/scripts/schema_install.sql
```

#### Scenario C: Embedding dimension shown is NOT 384

**Problem:** Wrong embedding model being used

**Solution:** Check your embedding model initialization in main.py:

```python
# Should be:
model_name = "sentence-transformers/all-MiniLM-L6-v2"  # 384 dimensions
```

### 3. Check Similarity Threshold

**Current Setting (after fix):**

```python
# main.py line ~176
db_search_tool = create_db_search_tool(supabase, embedding_model, match_threshold=0.1, match_count=5)
```

**What threshold means:**

- `0.0` = Return everything (no filtering)
- `0.1` = Very permissive (good for testing)
- `0.3` = Moderate (previous default - may be too strict)
- `0.5+` = Very strict (requires very similar content)

**Cosine similarity ranges:**

- `0.0` = Completely different
- `0.5` = Somewhat similar
- `0.8+` = Very similar
- `1.0` = Identical

### 4. Enhanced Logging

After the changes, you'll now see detailed logs:

```
INFO - DB Search: Generating embedding for query: 'rhode island resources'
INFO - DB Search: Embedding dimension: 384
INFO - DB Search: Embedding first 5 values: [-0.10156237, -0.071159825, ...]
INFO - DB Search: Searching Supabase with threshold=0.1, match_count=5...
INFO - DB Search: RPC call completed. Result type: <class 'postgrest.models.APIResponse'>
INFO - DB Search: Found 3 relevant documents
INFO - DB Search: Similarity scores: [0.654, 0.432, 0.321]
INFO - DB Search: Min=0.321, Max=0.654, Avg=0.469
INFO - DB Search: Returning 3 results as JSON
```

**If you see:**

```
WARNING - DB Search: No documents found with threshold 0.1. Consider lowering threshold.
```

**Then:** The embeddings might not be matching well. Try threshold=0.0 to see if ANY results exist.

## Common Issues & Solutions

### Issue 1: Database has data but RPC returns nothing

**Diagnosis:**

```sql
-- Check if embeddings exist
SELECT COUNT(*) FROM content_chunks WHERE embedding IS NOT NULL;

-- Check embedding dimensions
SELECT 
    source_url,
    array_length(embedding::real[], 1) as dim
FROM content_chunks 
LIMIT 5;
```

**If embeddings are NULL:** Re-run the vector loader

```bash
cd backend
uv run python src/utils/vector_loader.py
```

**If dimensions don't match (not 384):** Check your embedding model

### Issue 2: RPC Function Error

**Check function exists:**

```sql
SELECT routine_name 
FROM information_schema.routines 
WHERE routine_name = 'search_similar_documents';
```

**If missing:** Install schema

```bash
psql $DATABASE_URL -f backend/scripts/schema_install.sql
```

**If multiple versions exist:** Fix overload

```bash
psql $DATABASE_URL -f backend/scripts/fix_rpc_overload.sql
```

### Issue 3: Low Similarity Scores

Looking at your data row example:

```
"source_url":"https://dhs.ri.gov/"
"content": "...Rhode Island Department of Human Services..."
```

**Test queries that SHOULD match:**

- "rhode island human services"
- "DHS assistance programs"
- "SNAP benefits rhode island"
- "child care assistance"

**If these don't return results with threshold=0.1:**

1. Check if embedding model is loaded correctly
2. Verify embedding generation is working
3. Test RPC function manually

### Issue 4: Wrong Embedding Model

**Your data uses:** `sentence-transformers/all-MiniLM-L6-v2` (384 dimensions)

**Check your .env or model initialization:**

```python
# In main.py
model_name = "sentence-transformers/all-MiniLM-L6-v2"
embedding_model = HuggingFaceEmbeddings(model_name=model_name)
```

**DO NOT use models with different dimensions:**

- ❌ `all-mpnet-base-v2` (768 dims)
- ❌ `text-embedding-ada-002` (1536 dims)
- ✅ `all-MiniLM-L6-v2` (384 dims) ← Correct!

## Manual RPC Test

Test the RPC function directly in Supabase SQL Editor:

```sql
-- Generate a simple test embedding (384 dimensions, all 0.1)
SELECT * FROM search_similar_documents(
    array_fill(0.1, ARRAY[384])::vector,  -- Test embedding
    0.0,  -- Match threshold
    5     -- Match count
);
```

**Expected:** Should return some rows if data exists

**If error:** RPC function signature issue

## Verification Checklist

After applying fixes:

- [ ] `/test-db-search` endpoint returns results
- [ ] Similarity scores are reasonable (> 0.1 for relevant content)
- [ ] Embedding dimension is 384
- [ ] RPC function executes without errors
- [ ] Agent logs show "Found X relevant documents" (not 0)
- [ ] Actual queries through `/ask` return results from database

## Next Steps

1. **Run the test endpoint** to get diagnostic info
2. **Check the logs** for detailed embedding and search information
3. **Adjust threshold** if needed (currently set to 0.1)
4. **Verify RPC function** if you get errors
5. **Re-index data** if embeddings are missing or wrong dimensions

---

**Key Changes Made:**

- ✅ Lowered similarity threshold from 0.3 to 0.1
- ✅ Added `/test-db-search` diagnostic endpoint
- ✅ Enhanced logging in db_search tool
- ✅ Added similarity score reporting
- ✅ Added embedding dimension checks

**Test Command:**

```bash
# After starting backend
curl "http://localhost:8000/test-db-search?query=rhode%20island%20DHS"
```

This will tell you exactly what's happening with your search!
