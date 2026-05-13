# vecinita-scraper

Serverless scraping pipeline for Vecinita.

## Canonical scraper implementation

This directory ([`modal-apps/scraper/`](./)) is the **single** source of truth for scraper behavior
(crawl, job control, workers, and persistence). Other services (including **data-management-api**)
must integrate via **HTTP** only: configure `SCRAPER_SERVICE_BASE_URL` to the deployed scraper
origin and use `packages/service-clients` [`ScraperClient`](../data-management-api/packages/service-clients/service_clients/scraper_client.py)
instead of importing or copying orchestration from the legacy DM submodule checkout.

Remote integration contract: [`specs/003-consolidate-scraper-dm/contracts/dm-api-remote-service-integration.md`](../../specs/003-consolidate-scraper-dm/contracts/dm-api-remote-service-integration.md).

## Current architecture

- FastAPI control plane served directly from Modal
- Queue-driven worker pipeline for scrape, process, chunk, embed, and store stages
- PostgreSQL-backed job state and document persistence
- Direct service-to-service calls to embedding and model endpoints

## Crawl outcomes & smoke list (spec 011)

- **Direct fetch**: PDF and `text/*` URLs are fetched with `httpx` (bounded by `CrawlConfig.max_direct_fetch_bytes`) before the browser path. HTML stays on **Crawl4AI**.
- **Classification**: Failed HTML crawls attach structured JSON in `crawled_urls.error_message` (see `specs/011-fix-scraper-success/contracts/crawled-url-outcome.md`) plus optional `response_kind` / `failure_category` / `operator_summary` fields on gateway ingest.
- **Smoke URLs**: `smoke/crawl_smoke_urls.yaml` lists regression targets (SC-001 composition). Run live checks only with approval:
  `pytest tests/integration/test_smoke_crawl_live.py -m live` (default CI uses `-m "not live"`).

## Development

```bash
make dev-install
make test
make serve
```

`make test` and related test targets run with
`PYTHONWARNINGS=ignore:::requests` to suppress known non-blocking
`RequestsDependencyWarning` noise from `requests` import-time checks.

### Modal embedding message contract (Pact)

Consumer tests for the scraper → Modal embedding RPC surface live under
`tests/pact/` and write `pacts/vecinita-scraper-vecinita-embedding-modal.json`.
`tests/unit/test_embedding_client_modal_contract.py` asserts
`EmbeddingClient._modal_request` matches those shapes when Modal function
invocation is enabled.

Optional provider verification (after the pact file exists):

```bash
PACT_VERIFY_SCRAPER_EMBEDDING_MODAL_MESSAGE=1 pytest tests/pact/test_scraper_embedding_modal_message_pact_provider_verify.py
```

## Deployment

```bash
modal auth login
make deploy
```

### Render + Modal CLI (auth / secrets)

From the monorepo root, after `render login` and `modal` auth:

```bash
# Discover vecinita-data-management-api-v1 and dry-run PATCH of SCRAPER_API_KEYS from .env.prod.render
./scripts/sync_scraper_auth_render_modal.sh render --dotenv .env.prod.render --dry-run
export RENDER_API_KEY=...
./scripts/sync_scraper_auth_render_modal.sh render --dotenv .env.prod.render --yes

# Push / replace Modal secret vecinita-scraper-env (include all required keys in the file)
modal secret create vecinita-scraper-env --from-dotenv path/to/full-scraper-secret.env --force
# or the same via wrapper:
./scripts/sync_scraper_auth_render_modal.sh modal --from-dotenv path/to/full-scraper-secret.env --force
```

### Docker deploy

This service also ships with a Dockerfile and `render.yaml` for a Render Docker web-service deploy.

#### Docker / Render (monorepo parity)

Production **`vecinita-data-management-api-v1`** builds from the **repo root** blueprint with
`dockerfilePath: ./modal-apps/scraper/Dockerfile` and `dockerContext: ./modal-apps/scraper` (same paths as
Render). For baseline timings, cold vs warm-cache behavior, and smoke-run examples, use
[`specs/002-dm-api-docker-build/quickstart.md`](../../specs/002-dm-api-docker-build/quickstart.md).
Expect **repeat-edit** rebuilds (source-only changes) to be much faster than a full dependency
install once the stub dependency layer is warm; **cold** `--no-cache` builds still pull the full
stack and need plenty of free disk on the Docker data root.

The root monorepo [`render.yaml`](../../render.yaml) injects `DATABASE_URL` for `vecinita-data-management-api-v1` from the single shared `vecinita-postgres` resource via `fromDatabase` (internal `dpg-…-a` hostname is correct **on Render**). This directory’s [`render.yaml`](render.yaml) is for optional **standalone** Render deploys only: it does **not** provision a second database—set `DATABASE_URL` in the dashboard to your Postgres internal URL (or deploy from the repo root blueprint). If you run the same FastAPI image on **Modal**, add **`SCRAPER_API_KEYS`**, upstream URLs, and CORS settings to the Modal secret group **`vecinita-scraper-env`** (see `vecinita_scraper.api.app`). **Modal workers must set `MODAL_DATABASE_URL`** to the same database using Render’s [**external** Postgres URL](https://render.com/docs/postgresql-creating-connecting#external-connections) (public hostname + `sslmode=require`); internal hostnames from the blueprint **do not resolve** outside Render (`could not translate host name …`). `DATABASE_URL` in that secret may duplicate the external DSN or stay unset if `MODAL_DATABASE_URL` is set. GitHub Actions only supplies Modal CLI auth; it does not create or sync secrets for you. A stale or suspended DB still causes errors like `SSL connection has been closed unexpectedly`.

Required environment variables for the Docker / Render deployment:

- `DATABASE_URL`
- `SCRAPER_API_KEYS` — comma-separated Bearer secrets (or `DEV_ADMIN_BEARER_TOKEN` for one legacy token). **Omitting this in production causes immediate startup failure** (`ConfigError`).
- `EMBEDDING_UPSTREAM_URL`
- `CORS_ORIGINS`

Recommended environment variables:

- `OLLAMA_BASE_URL`
- `MODAL_TOKEN_ID`
- `MODAL_TOKEN_SECRET`
- `MODAL_WORKSPACE`

Local image build:

```bash
docker build -t vecinita-data-management-api-v1 .
docker run --rm -p 10000:10000 \
	-e PORT=10000 \
	-e ENVIRONMENT=development \
	-e DATABASE_URL=postgresql://user:pass@host:5432/db \
	-e SCRAPER_API_KEYS=local-dev-key \
	-e EMBEDDING_UPSTREAM_URL=https://example-embedding.modal.run \
	-e CORS_ORIGINS=http://localhost:3000 \
	vecinita-data-management-api-v1
```

## Runtime requirements

- `DATABASE_URL` (canonical Postgres DSN)
- `DB_URL` (optional; used only if `DATABASE_URL` is empty)
- `DATABASE_URL` (canonical Postgres DSN)
- `DB_URL` (optional; used only if `DATABASE_URL` is empty, same string otherwise)
- `EMBEDDING_UPSTREAM_URL`
- `OLLAMA_BASE_URL` when model-assisted extraction is enabled
- Modal credentials for deploy operations

## API

The control plane exposes job endpoints under `/jobs`.

- `POST /jobs`
- `GET /jobs/{job_id}`
- `GET /jobs`
- `POST /jobs/{job_id}/cancel`
