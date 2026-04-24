# Contract: `get_db()` persistence selection (Modal scraper)

**Canonical code**: `services/scraper/src/vecinita_scraper/core/db.py`  
**Operators**: `docs/deployment/RENDER_SHARED_ENV_CONTRACT.md`

## Preconditions

- **`_modal_function_running_in_cloud()`** — True inside Modal remote execution (see `modal.is_local()` and env fallbacks in code).

## Truth table (simplified)

| Modal cloud | `SCRAPER_GATEWAY_BASE_URL` + first `SCRAPER_API_KEYS` segment | `SCRAPER_ALLOW_DIRECT_POSTGRES_ON_MODAL` | Expected `get_db()` result |
|-------------|------------------------------------------------------------------|------------------------------------------|----------------------------|
| No | any | any | `PostgresDB()` (existing local/CI behavior) |
| Yes | both set | off | `GatewayHttpPipelinePersistence` |
| Yes | both set | on | `GatewayHttpPipelinePersistence` (HTTP branch wins first) |
| Yes | incomplete (missing URL or empty first key segment) | off | **`ConfigError`** with message referencing gateway + keys + contract doc |
| Yes | incomplete | on | `PostgresDB()` (escape hatch — **not** for production steady state) |

## HTTP pipeline active definition

**MUST** match implementation of `_use_gateway_http_pipeline()`:

- Non-empty stripped `SCRAPER_GATEWAY_BASE_URL`
- **AND** non-empty first segment of comma-split `SCRAPER_API_KEYS` (empty strings between commas do not count as a segment for “first”; implementation uses `_first_scraper_api_key_env()` — tests MUST lock this behavior).

## Invariants

- **I1**: When HTTP pipeline is active, workers **MUST NOT** open a new psycopg2 connection for `get_db()` return value.
- **I2**: When Modal cloud and HTTP pipeline inactive and bypass off, **`ConfigError` MUST be raised** before `PostgresDB()` construction (policy: no accidental direct DB from Modal).

## Test obligations (CI)

For each row that yields `ConfigError` or `GatewayHttpPipelinePersistence`, maintain a **pytest** case with monkeypatched `_modal_function_running_in_cloud` and controlled env vars (`services/scraper/tests/unit/test_get_db_modal_gateway.py` and extensions).
