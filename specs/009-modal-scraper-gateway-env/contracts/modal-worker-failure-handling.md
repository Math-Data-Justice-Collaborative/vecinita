# Contract: Modal worker exception handling vs persistence

**Affected entrypoints**:  
`scraper_worker`, `processor_worker`, `chunker_worker` in  
`services/scraper/src/vecinita_scraper/workers/{scraper,processor,chunker}.py`  
**Related**: `embedder_worker` uses a single upfront `get_db()` for the batch.

## C1 — No masked `ConfigError`

**MUST**: If `get_db()` raises **`ConfigError`** before any persistence handle is assigned for the job body, the worker’s outer `except` block **MUST NOT** call `get_db()` again solely to update job status in a way that replaces the original exception with an identical `ConfigError` chain.

**Rationale**: Operators and Modal logs must show **one** clear configuration failure, not “During handling of the above exception…” duplicates.

## C2 — Best-effort `FAILED` when client exists

**MUST**: If `run_*_job` (or equivalent) obtained a **`database`** instance and later raises a non-configuration exception, the worker **SHOULD** call `database.update_job_status(..., FAILED, ...)` when that object is in scope; if only `get_db()` at the start succeeded, reusing that handle is acceptable.

## C3 — `ConfigError` logging

**SHOULD**: When skipping DB update because persistence is unavailable (`ConfigError`), log **structured** context: `job_id`, and that the failure class is **configuration** (no secret values).

## C4 — Embedder batch

**NOTE**: `embedder_worker` obtains `db = get_db()` once before iterating batched payloads. A `ConfigError` there fails the entire batch entrypoint early — acceptable; document in tests if batch partial-failure behavior is ever required.

## Test obligations

- Unit test: simulate `run_scrape_job` raising `ConfigError` on first `get_db()` (monkeypatch `get_db` side effect: first call raises, or call `run_scrape_job` with no injected db and patch module) and assert worker handler **does not** produce a second `get_db()` invocation **or** that the raised exception preserves the original as the **context** / `__cause__` chain per chosen implementation.
- Prefer testing **`run_scrape_job` + handler snippet** via extracted helper if full `@app.function` is hard to invoke in CI.
