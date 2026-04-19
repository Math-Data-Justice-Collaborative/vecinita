# Phase 0 research: Scraper consolidation, remote DM API integration, gateway job stability

## 1. Root cause of live `5xx` on `/api/v1/modal-jobs/scraper*`

**Decision**: Treat **Postgres hostname reachability split** between **Render private network** and
**Modal** as the primary failure mode when logs show `could not translate host name "dpg-*"`.

**Rationale**:

- Baseline notes in `specs/001-gateway-live-schema/baseline-notes.md` already record this pattern.  
- `docs/deployment/RENDER_SHARED_ENV_CONTRACT.md` documents **`MODAL_SCRAPER_PERSIST_VIA_GATEWAY`**
  so Modal **submit** does not open DB with an internal Render hostname when the gateway owns row
  insert; list/get/cancel read Postgres on the gateway.  
- Implementation work must **verify** staging/production env sets match that contract and that any
  Modal worker stage still using Postgres uses **`MODAL_DATABASE_URL`** (or equivalent **externally
  resolvable** URL), not `DATABASE_URL` with internal-only hostnames.

**Alternatives considered**:

- **Code-only fix without env** — insufficient if Modal still receives internal DSNs.  
- **Return 200 with fake job** — violates honesty and contract tests.

## 2. Clarification B — data-management-api integrates via remote APIs only

**Decision**: DM API **must not** ship full `vecinita_scraper` / embedding / model **trees** as
submodules; it calls **deployed** service base URLs with documented OpenAPI (or shared OpenAPI
export) per capability.

**Rationale**: Recorded in spec **Clarifications / Session 2026-04-19**; reduces drift and clone
complexity (**FR-003**, **FR-004**, **SC-003**).

**Alternatives considered**:

- **Monorepo path dependencies** — rejected by stakeholder choice **B**.  
- **Hybrid** — explicitly out of scope for this feature’s integration style.

## 3. Submodule removal sequence

**Decision**: (1) Inventory all imports from `apps/backend/scraper-service`,
`embedding-service`, `model-service`. (2) Introduce **adapter module** in DM API that matches
current call shapes but delegates to **httpx** (or existing HTTP stack). (3) Run **parity** suite.
(4) Remove submodule paths and `.gitmodules` entries; update CI checkout steps that run
`git submodule update`.

**Rationale**: Minimizes broken-main risk; supports rollback by reverting adapter wiring only.

**Alternatives considered**:

- **Delete submodules first** — high churn, breaks builds immediately.

## 4. Parity testing — old vs new

**Decision**: Use **deterministic HTTP fixtures**: capture method, path, query, body hash, status,
and a **normalized JSON** projection (sorted keys, strip timestamps/UUIDs replaced with placeholders
or compare structural equality in tests). Store under `services/data-management-api/tests/parity/`
(or agreed location). Run **before** and **after** switch; CI job optional if secrets required, else
nightly staging.

**Rationale**: Gives evidence equivalent to “same behavior” without requiring identical wire bytes.

**Alternatives considered**:

- **Manual QA only** — rejected for regression risk at submodule removal.  
- **Full VCR to external services** — fragile; use mocks for CI, live parity for staging.

## 5. Schemathesis **errors** (server failures)

**Decision**: After **R1** env fixes, re-run `make test-schemathesis-cli`. Remaining `5xx` must be
triaged to application bugs vs misconfig. **Ask** `504`: track separately — increase agent budget,
optimize retrieval, or document streaming; gateway should return documented timeout body (already
observed).

**Rationale**: Aligns with **FR-005**, **SC-004**, **SC-005**.

## 6. Schemathesis **warnings** (404, schema mismatch, coverage)

**Decision**:

- **404 / missing test data**: Extend `backend/tests/schemathesis_hooks.py` (and env vars documented
  in `run_schemathesis_live.sh`) to register **real** `gateway_job_id`, document preview/download
  parameters, and scrape job IDs where the API requires existing resources.  
- **Schema validation mismatch**: For each operation listed in the report (`GET /api/v1/ask`,
  registry routes, documents, scrape cancel, etc.), reconcile **OpenAPI** constraints (formats,
  enums, required fields) with **FastAPI** / Pydantic validators so generated data is accepted.  
- **TraceCov / coverage below 100%**: Either raise implementation coverage (e.g. `POST
  /api/v1/scrape/reindex` currently disabled in config) or adjust **phase-specific** thresholds with
  documented rationale—**not** silently lowering global gates without review.

**Rationale**: Warnings blocked meaningful “green” signal in the attached run; fixing restores gate
value per constitution **Safety & quality**.

## 7. Single authoritative scraper source

**Decision**: **`services/scraper/src/vecinita_scraper`** remains canonical; DM API never vendors a
second copy.

**Rationale**: Matches spec **FR-003** and existing Render blueprint bias toward `services/scraper`
(see `002-dm-api-docker-build` research).
