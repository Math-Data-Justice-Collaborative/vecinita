# Quickstart: 011-fix-scraper-success

## Prerequisites

- Python **3.11+**  
- Repo root: `/root/GitHub/VECINA/vecinita`  
- `cd services/scraper` and install with **`uv sync`** or **`pip install -e ".[dev]"`** per service README.

## Run unit tests (no network)

```bash
cd services/scraper
pytest tests/unit -m "not live" -q
```

## Run smoke composition check (live, optional)

After **`smoke/crawl_smoke_urls.yaml`** exists and tests are wired:

```bash
cd services/scraper
pytest tests/ -m live -q --maxfail=1
```

Use **CI skip** by default (`-m "not live"`); enable live runs only with operator approval (public URLs, rate respect).

## Local Modal / worker (outline)

- Deploy or invoke **`scraper_worker`** with a job payload matching `ScrapeJobQueueData` (see `core/models.py`).  
- Verify **`store_crawled_url`** receives **`response_kind`** / **`failure_category`** when gateway supports them.

## Verify classification without Modal

- Unit-test **`document_fetcher`** / router with **`httpx.MockTransport`** and stub **`Crawl4AI`** results in **`test_crawl4ai_adapter`**.

## Related docs

- [spec.md](./spec.md) — acceptance and SC-001 smoke composition.  
- [data-model.md](./data-model.md) — category enums.  
- [contracts/crawled-url-outcome.md](./contracts/crawled-url-outcome.md) — persistence payload.
