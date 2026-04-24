# Data model — configuration & job status (009)

**Scope**: Logical configuration and job state touched by Modal scraper workers and gateway HTTP persistence. Not a new database schema.

## Entity: Worker persistence mode

| Field | Description |
|-------|-------------|
| `runtime` | `modal_cloud` \| `non_modal` (derived from `_modal_function_running_in_cloud()`) |
| `http_pipeline_active` | True when `SCRAPER_GATEWAY_BASE_URL` is non-empty **and** first segment of `SCRAPER_API_KEYS` is non-empty |
| `direct_postgres_allowed` | True when `SCRAPER_ALLOW_DIRECT_POSTGRES_ON_MODAL` is truthy (debug escape hatch) |
| `postgres_client_active` | True when `http_pipeline_active` is False and policy allows `PostgresDB()` (local, non-Modal cloud, or escape hatch) |

**Validation rules**:

- If `runtime == modal_cloud` and not `http_pipeline_active` and not `direct_postgres_allowed` → **`get_db()` raises `ConfigError`** (no `PostgresDB` instance).
- If `http_pipeline_active` → `get_db()` returns **`GatewayHttpPipelinePersistence`** regardless of DSN env presence for pipeline code paths.

## Entity: Gateway ingest authorization list

| Field | Description |
|-------|-------------|
| `raw` | Comma-separated secrets in `SCRAPER_API_KEYS` (gateway and Modal must match string) |
| `segments` | Non-empty stripped parts of `raw` |
| `pipeline_token` | First segment of `segments`; sent as `X-Scraper-Pipeline-Ingest-Token` from workers |

**Validation rules**:

- Empty `raw` or no segments → HTTP pipeline mode is **inactive** even if base URL is set.
- Gateway must accept **any** segment for ingest auth (per deployment contract); worker sends **first** only.

## Entity: Scrape job (status slice)

| State | Meaning |
|-------|---------|
| `FAILED` | Terminal failure; `error_message` may hold exception string |
| (other) | As existing `JobStatus` enum in scraper package |

**Transitions relevant to this feature**:

- On processing exception **with** a persistence client → transition to `FAILED` via `update_job_status`.
- On **`ConfigError`** from missing gateway/keys when **no** client was acquired → **no** guaranteed `FAILED` row update on Modal (gateway or operator must infer from logs); after code fix, logs remain primary signal without chained `ConfigError`.

## Relationships

- **Worker persistence mode** determines which implementation backs **`database`** in `run_*_job`.
- **Gateway ingest list** must match between **Render gateway** env and **Modal** secret group for HTTP pipeline mode.
