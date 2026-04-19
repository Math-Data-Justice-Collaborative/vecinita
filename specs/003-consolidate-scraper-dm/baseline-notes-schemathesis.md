# Live Schemathesis baseline — feature `003-consolidate-scraper-dm`

**Purpose**: Anchor failing operations, warnings, and (later) schema-mismatch operation names for **T001** / **T037**. Update as runs complete.

## Last captured run (template — fill from CI or local)

| Field | Value |
|-------|--------|
| Gateway base URL | `https://vecinita-gateway-lx27.onrender.com` (example from 2026-04-19 run) |
| Date (UTC) | 2026-04-19 |

### Server-error class failures (examples)

| Operation | Symptom | Notes |
|-----------|---------|--------|
| `POST /api/v1/modal-jobs/scraper` | 500 | Postgres hostname not resolvable from Modal (`dpg-*` / DNS) when misconfigured |
| `GET /api/v1/modal-jobs/scraper` | 500 | Same persistence path |
| `GET /api/v1/modal-jobs/scraper/{job_id}` | 500 | Same |
| `POST /api/v1/modal-jobs/scraper/{job_id}/cancel` | 500 | Same |
| `GET /api/v1/ask` | 504 | Agent / gateway timeout |

### Warnings (non-fatal)

- **404 / missing test data**: `DELETE/GET …/modal-jobs/registry/{gateway_job_id}`, `GET …/documents/download-url`, `GET …/documents/preview`, etc.
- **Schema validation mismatch**: several operations (see JUnit / HTML report).
- **TraceCov / coverage**: thresholds below 100% on some keywords (e.g. `POST /api/v1/scrape/reindex`).

### Schema-mismatch operation list (**T037** input)

Anchored set of **seven** gateway operations where OpenAPI query/response models were tightened
(2026-04-19) so Schemathesis/Hypothesis generates fewer cases that FastAPI rejects before hitting the
wire (enums / `min_length` / documented query bounds). Re-run **T001** after the next full live suite
to append any *additional* mismatch rows from JUnit/HTML.

| # | Operation | Alignment applied |
|---|-----------|-------------------|
| 1 | `GET /api/v1/ask` | `GatewayAskQueryParams` — `Literal` tag mode, `min_length` on `question` (**T033**) |
| 2 | `GET /api/v1/ask/stream` | Same query bundle as **(1)** |
| 3 | `GET /api/v1/documents/overview` | `DocumentsOverviewQueryParams.tag_match_mode` → `Literal["any","all"]` |
| 4 | `GET /api/v1/documents/tags` | `DocumentsTagsQueryParams.locale`, `DocumentsTagRow.locale`, `DocumentsTagsResponse.locale` → `Literal["en","es"]` |
| 5 | `GET /api/v1/modal-jobs/scraper` | Optional `user_id` query: `Query(min_length=1)` when present |
| 6 | `GET /api/v1/modal-jobs/registry/{gateway_job_id}` | `GatewayModalRegistryRecord.gateway_job_id` → `min_length=1` |
| 7 | `GET` / `POST` … **modal-jobs scraper** job bodies | `GatewayModalScrapeJobBody.job_id` → `min_length=1` (list/get/cancel/submit responses) |

### T041 Spec rollout status

**Agreed partial milestone (2026-04-19)** — do **not** set `spec.md` to **Complete** until all release
gates below are green or carry a **signed waiver** in this file.

| Criterion | State |
|-----------|--------|
| FR-001–FR-007 | Engineering in place; **T034** ask-only Schemathesis probe green; FR-001/FR-005 live proof still blocked on **T016** until modal-jobs `5xx` clears (**T014** curl shows **500** on list) |
| SC-002 | Contributor docs point at single scraper path (see root `CONTRIBUTING.md` / scraper README) |
| SC-003 | Nested DM backend submodules removed (**T027**) |
| SC-001 (**T015**) | Smoke script green in CI when enabled |
| SC-004 / FR-005 | Live Schemathesis gate — **T016** / waiver |
| SC-005 | Benchmark + waiver row if below threshold — **T034** / **T035** |
| FR-006 | Correlation id in Modal metadata — **T011**; document key in this file when verified live |

### Staging curl checks (**T014**)

Steps **1–4** in [quickstart.md](./quickstart.md) §1 remain **operator** checks on Render / Modal
dashboards (env contract). **§1 step 5** smoke (automated probe, UTC **2026-04-19**):

| Target | HTTP | Notes |
|--------|------|--------|
| `GET https://vecinita-gateway-lx27.onrender.com/api/v1/health` | **200** | Cold start tolerated (`--max-time 45`) |
| `GET https://vecinita-gateway-lx27.onrender.com/api/v1/modal-jobs/scraper` | **500** | Matches server-error table above (persistence / Modal DB split); **not** a green **T016** gate until env is healthy |

### Ask-focused Schemathesis (**T034**)

Gateway-only run with `SCHEMATHESIS_GATEWAY_INCLUDE_PATH_REGEX='/api/v1/ask$'`,
`SCHEMATHESIS_GATEWAY_MAX_EXAMPLES=6`, `SCHEMATHESIS_COVERAGE=0`, `DATA_MANAGEMENT_SCHEMA_URL=""` (UTC **2026-04-19**):

- **Cases**: 122 generated, **122 passed** (`not_a_server_error`).
- **Scope**: `GET /api/v1/ask` only (no stream pass in this filter).
- **Script**: set `SCHEMATHESIS_GATEWAY_INCLUDE_PATH_REGEX` in `backend/scripts/run_schemathesis_live.sh` (documented header); invoke via `make test-schemathesis-cli` from repo root.

### Live modal-jobs gate (**T016**)

**T016** (zero server-error class failures on `/api/v1/modal-jobs/scraper*`) is **not** satisfied on
`vecinita-gateway-lx27` while `GET /api/v1/modal-jobs/scraper` returns **500** (see **T014** table).
Re-run full `make test-schemathesis-cli` after Render/Modal `DATABASE_URL` / `MODAL_DATABASE_URL`
alignment; document any env-only waiver with owner sign-off here.

### Remote client parity (**T026**)

- `services/data-management-api/tests/parity/test_remote_clients_parity.py` is exercised from repo root via **`make test-backend-unit`** (PYTHONPATH includes `service-clients` + `shared-schemas`). Last green run bundled with backend unit suite: **2026-04-19** (CI).

### Submodule → HTTP client migration (**T025** / **T027**)

- `rg vecinita_scraper services/data-management-api/packages` → **no** matches.
- **T027 (2026-04-19)**: Nested DM API submodules `apps/backend/{scraper,embedding,model}-service` removed; `.gitmodules` retains `apps/frontend` only. Root `render.yaml` already builds the data-management API image from monorepo `services/scraper`; standalone DM `Dockerfile` clones [vecinita-scraper](https://github.com/Math-Data-Justice-Collaborative/vecinita-scraper) at build time.

## Gateway → agent timeout chain (**T031** — measured in code, 2026-04-19)

Source: `backend/src/api/router_ask.py`.

| Hop | Mechanism | Default (seconds) | Env override |
|-----|-----------|--------------------:|--------------|
| Gateway `GET /api/v1/ask` → agent `GET /ask` | `httpx.AsyncClient.get(..., timeout=httpx.Timeout(...))` | read **120**, connect **10**, pool **10** | `AGENT_TIMEOUT` (read; must be `> 0`), `AGENT_HTTP_CONNECT_TIMEOUT`, `AGENT_HTTP_POOL_TIMEOUT` |
| Gateway `GET /api/v1/ask/stream` → agent `GET /ask-stream` | `client.stream(..., timeout=httpx.Timeout(...))` | read **120**, connect **10**, pool **10** | `AGENT_STREAM_TIMEOUT` (read), same connect/pool envs |
| Shared agent client | `httpx.AsyncClient` with connection limits only; **no** global read timeout on the client object | — | Per-request `httpx.Timeout` on each call |

Notes:

- On `httpx.TimeoutException`, the non-streaming route maps to **504** with a generic timeout message (see `router_ask.py`).
- The agent service’s own graph / tool timeouts are **not** re-derived here; treat **SC-005** as the product gate until agent internals are profiled separately.
- **T033** (2026-04-19): `GatewayAskQueryParams` uses `Literal["any","all"]` for `tag_match_mode` and `min_length=1` on `question` so OpenAPI matches FastAPI validation and Schemathesis rejects fewer generated cases on `GET /api/v1/ask` / `…/stream`.

## Ask SLO agreement (**T031**)

| Item | Owner | Target | Status |
|------|-------|--------|--------|
| Beyond **SC-005** (20 questions × 3 days, ≥18 successes/day) | _TBD platform owner_ | Record p95/p99 for `GET /api/v1/ask` once staging metrics exist | _Pending_ |
| Review date | _TBD_ | After first week of **T035** logs | _Pending_ |

## Correlation ID payload key (**T011** / contract)

_After implementation: document the JSON key used under `metadata` for Modal submit (default: `correlation_id`)._

## TraceCov / `SCHEMATHESIS_COVERAGE_FAIL_UNDER` (**T038**)

- **Release / PR gate**: keep the default **100** TraceCov floor on full schema pytest runs where the team policy requires it (see root [`TESTING_DOCUMENTATION.md`](../../TESTING_DOCUMENTATION.md)).
- **Local debugging only**: for noisy operations (e.g. `POST /api/v1/scrape/reindex` excluded until `REINDEX_SERVICE_URL` is healthy), you may export a **lower** `SCHEMATHESIS_COVERAGE_FAIL_UNDER` for `schemathesis run` / `run_schemathesis_live.sh` sessions; **do not** commit a lowered gate to CI without reviewer sign-off and a note in this file.
