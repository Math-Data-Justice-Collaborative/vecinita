# Connectivity gates (multi-app / static frontend)

Canonical reference for **browser-reachable** deployments and **cross-service wiring**.
Every pipeline skill **00–15** must apply the obligations in [§Pipeline stages 00–15](#pipeline-stages-00-15)
for the current stage — not only 12–13.

Backend-only smokes (H1–H3 `curl`) are **necessary but not sufficient** for “users can use the UI.”

**Orchestrator:** [pipeline/SKILL.md](pipeline/SKILL.md) enforces phase gates that reference this file.
**Cross-cutting:** [considerations.md](considerations.md) §9.

## Why this exists

| Check type | Proves | Does **not** prove |
|------------|--------|---------------------|
| `GET /health` on API | Process up, server-side deps | Browser can call API |
| `POST /api/v1/ask` via httpx | RAG path from operator shell | `VITE_*` baked into frontend |
| Vitest with mocked `fetch` | Component logic | Cross-origin CORS on staging |
| `tests/integration` (in-process) | Server-side wiring | Browser preflight / bundle URLs |

Static frontends call APIs on **different origins** (`*.ondigitalocean.app`, `*.modal.run`).
Without `CORSMiddleware` (or a same-origin BFF per TP-001), browsers block requests even when
`curl` succeeds.

## Test & health tier matrix

| Tier | Name | When | Command / artifact | Blocking |
|------|------|------|-------------------|----------|
| H0 | Local unit | CI, 07 | `pytest tests/unit` | CI |
| **H0c** | **CORS policy (in-process)** | CI, 07 | `pytest tests/unit/test_cors_policy.py` | **CI** |
| **H0i** | **Integration wiring** | CI, 07, 10 | `pytest tests/integration` | **CI** |
| H1 | API liveness | 13, 15 | `GET {API}/health` | 13 |
| H2 | DB ready | 13, 15 | `staging_h2.py` / Alembic | 13 |
| H3 | API RAG smoke | 13, 15 | `POST {CHAT}/api/v1/ask` | 13 |
| **H4** | **CORS preflight (live)** | 12, **13**, 15 | `tests/smoke/test_staging_connectivity.py -m live` | **13** (when URLs set) |
| **H5** | **Frontend bundle wiring** | 12, **13**, 15 | `scripts/deploy/verify_connectivity.sh` | **13** (when URLs set) |
| H6 | Browser UJ | 10 T3, 15 deep | browser MCP / Playwright | Advisory unless user requires |

**13-deploy-smoke is not complete** until H1–H3 **and** H4–H5 pass (or documented waiver in
`docs/deploy-checklist.md` with user AskQuestion approval).

## Pipeline stages 00–15

| Stage | Connectivity obligations |
|-------|------------------------|
| **00-context** | Capture topology: static UI vs API hosts, Modal↔DO paths, existing CORS/BFF; flag “browser integration risk” in context brief |
| **01-requirements** | Specs must cover: `VITE_*` build-time URLs, `VECINITA_CORS_ORIGINS`, UJ browser steps; **test-plan** defines H0c/H0i/H4/H5; **deployment-integration** § browser wiring |
| **02-verify-plan** | Audit statements: multi-origin UI requires CORS or BFF; Vitest ≠ production connectivity; reject “health-only smoke = E2E done” |
| **03-plan-tooling** | Guardrails reference this file; scope rule blocks UI features without connectivity test plan |
| **04-tech-plan** | Execution plan tasks: `configure_cors`, integration tests, `verify_connectivity.sh`; ADR if deferring gateway (TP-001) |
| **05-verify-tech** | Verify tech plan includes H0c/H0i/H4/H5 tasks and secrets matrix rows |
| **06-tech-tooling** | CI runs `test_cors_policy.py`; `tests/smoke/test_staging_connectivity.py` present; document staging env vars |
| **07-build** | Browser-facing APIs use `configure_cors`; extend H0c/H0i tests per app; task not done until green |
| **08-verify-build** | Blocking: H0c + integration suite; advisory: connectivity modules exist |
| **09-qa** | Report H0c pass/fail; H4–H5 advisory or blocking if staging URLs in env |
| **10-e2e** | T0 = in-process e2e; T2 = 13’s H1–H5; record T3/browser separately; mocks ≠ connectivity |
| **11-verify-impl** | UI features (F11/F12): require connectivity plan or H4/H5 waiver before approve |
| **12-verify-deploy** | Agent 6 + checklist: CORS origins, `VITE_*` matrix, scripts exist |
| **13-deploy-smoke** | Pre: H0c; post: `verify_connectivity.sh` (H4–H5 blocking) |
| **14-hotfix** | Classify “Failed to fetch” as connectivity first; repro may use H4 assertion |
| **15-service-health** | Post-deploy: H4–H5 on UI complaints; H0i on integration regressions |

Stages **16-evolve** and **17-retrospective** must re-apply the rows above for any new UI or API surface.

## Topology (Vecinita staging)

```text
Browser
  ├─ Chat UI (DO static)  --CORS-->  ChatRAG backend (DO)
  │                                      ├─ Postgres
  │                                      ├─ Modal embed
  │                                      └─ Modal LLM
  └─ Admin UI (DO static) --CORS-->  Modal data-mgmt (/jobs, Modal-Key)
                         --CORS-->  Internal write API (/internal/v1/..., Bearer)
```

## Wiring checklist

### Build-time (`VITE_*` — DO BUILD_TIME secrets)

| Frontend app | Variable | Must point to |
|--------------|----------|---------------|
| `vecinita-chat-rag-frontend` | `VITE_VECINITA_CHAT_API_URL` | ChatRAG backend ingress |
| `vecinita-admin-frontend` | `VITE_VECINITA_ADMIN_API_URL` | Modal data-mgmt ASGI URL |
| `vecinita-admin-frontend` | `VITE_VECINITA_MODAL_PROXY_KEY` | `VECINITA_MODAL_PROXY_KEY` on Modal |
| `vecinita-admin-frontend` | `VITE_VECINITA_CORPUS_API_URL` | Internal write API ingress |
| `vecinita-admin-frontend` | `VITE_VECINITA_CORPUS_API_KEY` | `VECINITA_INTERNAL_API_KEY` |

**H5:** live JS bundle contains those hosts (not `localhost`, not empty).

### Run-time (`VECINITA_CORS_ORIGINS` — API services)

Comma-separated frontend origins (scheme + host, no path). Example:

```text
https://vecinita-chat-rag-frontend-jnt8o.ondigitalocean.app,https://vecinita-admin-frontend-ef4ob.ondigitalocean.app
```

| API app | Must allow |
|---------|------------|
| ChatRAG backend | Chat frontend origin |
| Internal write API | Admin frontend origin |
| Modal data-mgmt | Admin origin + `Modal-Key` header |

### CORS HTTP methods (browser verbs)

`configure_cors()` `allow_methods` must include **every HTTP verb** exposed on browser-facing
routes — not only GET/POST. Browsers send OPTIONS preflight for DELETE, PUT, PATCH, etc.

| App | Route verbs (v1) | Required in `allow_methods` |
|-----|------------------|----------------------------|
| ChatRAG backend | GET, POST (stream) | GET, POST, OPTIONS |
| Internal write API | GET, POST, DELETE | GET, POST, DELETE, OPTIONS |
| Modal data-mgmt | GET, POST (jobs) | GET, POST, OPTIONS |

**H0c:** For each verb, OPTIONS with `Access-Control-Request-Method: <VERB>` must return 200 and
list `<VERB>` in `access-control-allow-methods` (`tests/unit/test_cors_policy.py`).

**H4 (live):** Mirror H0c on staging URLs; internal-write-api must include DELETE preflight on
`/internal/v1/documents/{id}` (`test_h4_write_api_cors_preflight_delete_document`).

Source: BUG-2026-05-22 — admin DELETE Failed to fetch when DELETE was omitted from CORS.

## Commands

```bash
# CI / pre-deploy (blocking)
uv run pytest tests/unit/test_cors_policy.py tests/integration -q

# Staging post-deploy (blocking for 13 when env set)
export VECINITA_STAGING_CHAT_URL=...
export VECINITA_STAGING_WRITE_URL=...
export VECINITA_STAGING_CHAT_FRONTEND_URL=...
export VECINITA_STAGING_ADMIN_FRONTEND_URL=...
export VECINITA_STAGING_ADMIN_API_URL=...   # Modal data-mgmt

bash scripts/deploy/verify_connectivity.sh
# or: uv run pytest tests/smoke/test_staging_connectivity.py -m live -v

uv run --with pydo --with pyyaml scripts/deploy/do_apps.py urls --frontend
```

## Failure signatures

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| UI “Failed to fetch” | Missing CORS origin | `VECINITA_CORS_ORIGINS` + redeploy APIs |
| UI “Failed to fetch”, origin OK, DELETE/PUT fails | Missing verb in `allow_methods` | Add verb to `cors.py` + H0c/H4 OPTIONS test (§CORS HTTP methods) |
| “Set VITE_VECINITA_*” in UI | Empty build secrets | DO BUILD_TIME secrets + redeploy **frontend** |
| Bundle has `localhost` | Wrong `VITE_*` at build | `sync-secrets` + `force_build` |
| H3 pass, H4 fail | Backend-only validation | `verify_connectivity.sh` |
| Integration pass, UI fail | No H4/H5 run | Run live connectivity tier |

## Artifact checklist (must exist before 13)

| Artifact | Path |
|----------|------|
| CORS helper | `packages/shared-schemas/vecinita_shared_schemas/cors.py` |
| H0c tests | `tests/unit/test_cors_policy.py` |
| H0i tests | `tests/integration/**` |
| H4–H5 tests | `tests/smoke/test_staging_connectivity.py` |
| Operator script | `scripts/deploy/verify_connectivity.sh` |
| Secrets matrix | `docs/staging-secrets-matrix.md` (CORS + VITE rows) |
| Runbook | `docs/staging-runbook.md` (H4–H5) |
