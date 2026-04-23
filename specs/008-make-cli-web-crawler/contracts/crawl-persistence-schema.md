# Contract: Crawl persistence (SQL)

This contract mirrors [data-model.md](../data-model.md). Exact table names follow repo migration naming (e.g. `vecina_crawl_runs`); logical names below.

## Table: `crawl_runs`

- **Primary key**: `id` UUID.  
- **Immutability**: rows updated only for lifecycle fields `finished_at`, `status`, counters (`pages_*`) while run progresses; **no deletes** during normal operation.

## Table: `crawl_fetch_attempts`

- **Append-only**: `INSERT` only from application code; no `UPDATE`/`DELETE` in crawler (operator maintenance migrations may archive old rows per assumption in spec).  
- **FK**: `crawl_run_id` → `crawl_runs.id` `ON DELETE CASCADE` acceptable for dev cleanup only; production prefers retain history and forbid cascade delete from app.

## Invariants

1. Every `crawl_fetch_attempts` row has non-null `crawl_run_id`, `canonical_url`, `attempted_at`, `outcome`, `retrieval_path`.  
2. `outcome=skipped` implies non-null `skip_reason`.  
3. `document_format=pdf` implies `pdf_extraction_status IN ('ok','failed','skipped_size')` when `outcome=success` or `partial`.  
4. `raw_artifact` is null when `raw_omitted_reason` is set.

## Latest-success query (reference)

```sql
SELECT DISTINCT ON (canonical_url) *
FROM crawl_fetch_attempts
WHERE crawl_run_id = $1 AND outcome = 'success'
ORDER BY canonical_url, attempted_at DESC;
```

(Global cross-run variant: add `crawl_run_id` filter or use view defined in `quickstart.md`.)
