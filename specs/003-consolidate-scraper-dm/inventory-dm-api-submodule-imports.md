# DM API submodule import inventory — `003-consolidate-scraper-dm`

Generated for **T002**. Python references to `vecinita_scraper` / submodule trees live **inside**
`services/data-management-api/apps/backend/scraper-service/` (the git submodule checkout). No
matches were found under `services/data-management-api/` **outside** that tree for path strings
`apps/backend/scraper-service`, `embedding-service`, or `model-service` in import statements (those
paths are filesystem locations, not import paths).

## Submodule: `apps/backend/scraper-service`

Primary package: `vecinita_scraper` (relative imports within the checkout). Representative files:

| Path | Role |
|------|------|
| `.../scraper-service/src/vecinita_scraper/api/server.py` | FastAPI app factory |
| `.../scraper-service/src/vecinita_scraper/services/job_control.py` | Modal/job orchestration |
| `.../scraper-service/src/vecinita_scraper/core/db.py` | Postgres persistence |
| `.../scraper-service/tests/**` | Unit/integration tests importing `vecinita_scraper.*` |

## HTTP clients (canonical remote integration)

| Path | Role |
|------|------|
| `packages/service-clients/service_clients/scraper_client.py` | httpx client → deployed scraper |
| `packages/service-clients/service_clients/embedding_client.py` | httpx client → embedding service |
| `packages/service-clients/service_clients/model_client.py` | httpx client → model service |

## **T003** audit (high level)

- **ScraperClient**: `scrape`, `health` — extend when inventory shows additional REST surfaces needed by DM UI.
- **EmbeddingClient** / **ModelClient**: mirror scraper pattern when DM consumers require more than health + single call.

_Re-run `rg vecinita_scraper services/data-management-api` after submodule removal (**T027**) to confirm zero unexpected imports._

**T019 (2026-04-19)**: `rg vecinita_scraper` under `services/data-management-api/packages/` is empty; under `services/data-management-api/apps/` matches only `apps/backend/scraper-service/`. No DM consumers outside the submodule import `vecinita_scraper` today.

---

## T003 — Service client coverage audit

| Capability | Client module | Current methods | Gap vs submodule tree |
|------------|---------------|-----------------|------------------------|
| Scraper | `service_clients/scraper_client.py` | `scrape`, `health` | Submodule exposes full REST + Modal job APIs; extend client methods as DM consumers migrate off in-tree calls. |
| Embedding | `service_clients/embedding_client.py` | `embed` pattern + `health` | Confirm parity with any DM routes still calling submodule embedding HTTP. |
| Model | `service_clients/model_client.py` | `predict` pattern + `health` | Same as embedding. |

**Conclusion**: No extra RPC methods are strictly required until **T023–T025** map concrete DM consumer calls; use **T002** paths + grep results to extend clients incrementally.
