# Data model: Active crawl (008)

Entities align with [spec.md](./spec.md) **Key Entities** and functional requirements FR-005, FR-010, FR-011, FR-012.

## `crawl_runs`

| Field | Type | Required | Notes |
|-------|------|----------|--------|
| `id` | UUID | yes | PK |
| `started_at` | timestamptz | yes | |
| `finished_at` | timestamptz | no | null while running |
| `status` | text | yes | `running` \| `completed` \| `failed` \| `cancelled` |
| `config_snapshot` | jsonb | yes | caps, seed paths, heuristic thresholds, version |
| `pages_fetched` | int | yes | default 0 |
| `pages_skipped` | int | yes | robots / off-scope / dedupe |
| `pages_failed` | int | yes | |
| `initiator` | text | no | e.g. `cli`, hostname |
| `notes` | text | no | operator-visible short message on fatal error |

## `crawl_fetch_attempts` (append-only)

One row per **URL attempt** per **run** (same canonical URL across runs → multiple rows).

| Field | Type | Required | Notes |
|-------|------|----------|--------|
| `id` | bigserial | yes | PK |
| `crawl_run_id` | UUID | yes | FK → `crawl_runs.id` |
| `canonical_url` | text | yes | normalized URL for dedupe + audit |
| `requested_url` | text | yes | original before redirects |
| `final_url` | text | no | after redirects |
| `seed_root` | text | yes | registrable domain / seed this branch belongs to |
| `depth` | int | yes | hops from that seed root |
| `attempted_at` | timestamptz | yes | |
| `http_status` | int | no | if HTTP applied |
| `outcome` | text | yes | `success` \| `partial` \| `failed` \| `skipped` |
| `skip_reason` | text | no | e.g. `off_domain`, `robots`, `max_depth` |
| `retrieval_path` | text | yes | `static` \| `playwright` \| `recursive_loader` \| `mixed` — mirror actual `SmartLoader` branch |
| `document_format` | text | no | `html` \| `pdf` \| `other` |
| `extracted_text` | text | no | primary text (FR-010) |
| `raw_artifact` | bytea | no | HTML/PDF bytes when retention allows |
| `raw_omitted_reason` | text | no | size / policy / operator `no_raw` |
| `content_sha256` | text | no | |
| `pdf_extraction_status` | text | no | `na` \| `ok` \| `failed` |
| `error_detail` | text | no | stack or HTTP body snippet, capped |

### Indexes (recommended)

- `(crawl_run_id, attempted_at DESC)`  
- `(canonical_url, attempted_at DESC)` for “latest successful per URL” views  
- `(seed_root, crawl_run_id)` for per-host reporting  

### Views (documented in quickstart)

- **`v_crawl_latest_success`**: `DISTINCT ON (canonical_url)` ordered by `attempted_at` desc where `outcome = 'success'` (per operator choice: global or scoped to one `crawl_run_id`).

## Relationships

- `crawl_runs` 1 — N `crawl_fetch_attempts`  
- No FK from `document_chunks` required for MVP (optional future: `crawl_fetch_attempt_id` in metadata jsonb on chunks).

## Validation rules

- `extracted_text` empty on `outcome=success` for HTML requires `partial` or explicit `extraction_empty` flag (planner: add `extraction_notes` if needed in migration).  
- `raw_artifact` null when `raw_omitted_reason` set.  
- `pdf_extraction_status` required when `document_format=pdf`.
