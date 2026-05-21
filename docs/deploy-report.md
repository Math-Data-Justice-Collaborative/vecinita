# Deploy Report

> Date: 2026-05-20 (connectivity gates validated 2026-05-21)
> Status: **deployed**
> Primary URL: https://vecinita-chat-rag-backend-jvqso.ondigitalocean.app

## Pre-Deploy

- Checklist: partial pass with documented T3 post-deploy waiver ([deploy-checklist.md](deploy-checklist.md))
- T0 e2e: **PASS** (11/11, `pytest tests/e2e/ -m "e2e and not live"`)
- Migrations: **PASS** (`alembic upgrade head` on `vecinita-staging`)

## Deployment

| Component | Command / tool | Result |
|-----------|----------------|--------|
| Modal | `scripts/deploy/modal.sh` | SUCCESS |
| DO apps | `scripts/deploy/do_apps.py` (pydo) | SUCCESS |
| Postgres | pydo `create_cluster` | SUCCESS |

**ChatRAG backend fix:** Build without `uv sync --group dev` produced an image missing `uvicorn`. Restored `build_command: uv sync --group dev`; deploy **ACTIVE** in ~2 min.

## Smoke Tests

| Test | Status | Response Time |
|------|--------|---------------|
| H1 ChatRAG `/health` | PASS | ~830 ms |
| H1 Write API `/health` | PASS | — |
| H2 DB + Alembic | PASS | — |
| H3 `POST /api/v1/ask` | PASS | ~4911 ms |
| H4 ChatRAG CORS preflight | PASS | — |
| H4 Write API CORS preflight | PASS | — |
| H4 Modal data-mgmt CORS | **WAIVER** | 401 — see §Connectivity |
| H5 Chat frontend bundle wiring | PASS | — |
| H5 Admin frontend bundle wiring | PASS | — |

H3 returned a valid `answer` + `language: en` with fixture `sources` on re-validate (~1.7s warm; first cold run may 504 until Modal LLM scales up).

### Connectivity Gates (H4/H5) — 2026-05-21

**CORS setup:** Pushed `VECINITA_CORS_ORIGINS` to ChatRAG backend and internal write API via live spec update (pydo `apps.update` with plaintext values). DO's encrypted `EV[...]` values cannot be roundtripped via `apps.update` — must provide plaintext for all secrets when updating spec.

| Gate | Status | Detail |
|------|--------|--------|
| H0c local CORS | PASS | `pytest tests/unit/test_cors_policy.py` (3 pass, 1 skip) |
| H4 ChatRAG backend | PASS | `Access-Control-Allow-Origin: https://vecinita-chat-rag-frontend-jnt8o.ondigitalocean.app` |
| H4 Internal write API | PASS | `Access-Control-Allow-Origin: https://vecinita-admin-frontend-ef4ob.ondigitalocean.app` |
| H4 Modal data-mgmt | **WAIVER** | Modal `requires_proxy_auth` intercepts OPTIONS preflight at proxy (401). Architectural limitation — browsers never send auth on preflight per CORS spec. User-approved waiver. |
| H5 Chat frontend bundle | PASS | Bundle contains ChatRAG backend host |
| H5 Admin frontend bundle | PASS | Bundle contains write API + Modal data-mgmt hosts |

**H4 Modal waiver rationale:** Modal's proxy auth operates before the ASGI app receives requests. OPTIONS preflights carry no auth per [CORS spec](https://developer.mozilla.org/en-US/docs/Glossary/Preflight_request). Resolution deferred — options: app-level auth (remove `requires_proxy_auth`, check Modal-Key in FastAPI middleware), or proxy admin calls through DO. Admin UI functionality that calls Modal data-mgmt directly will need `no-cors` mode or a DO proxy in production.

### Re-validation (2026-05-20)

| Check | Result |
|-------|--------|
| T0 `pytest tests/e2e/ -m "e2e and not live"` | PASS |
| `staging_smoke.sh` H1–H3 | PASS |
| T3 `pytest tests/smoke -m live` | PASS (11/11) |
| Code at validation | `c4bc847` on `main` |

### Re-deploy (2026-05-20)

| Step | Command | Result |
|------|---------|--------|
| Modal | `scripts/deploy/modal.sh` | SUCCESS (embedding, data-mgmt, LLM) |
| DO apps | `do_apps.py deploy --name` ×4 (`force_build`) | SUCCESS — all ACTIVE |
| Post-smoke | H1–H3 + T3 live | PASS after LLM warm (~19s cold start) |

### CORS redeploy (2026-05-21)

| Step | Detail |
|------|--------|
| `apps.update` ChatRAG | Added `VECINITA_CORS_ORIGINS` with plaintext value; auto-deploy ACTIVE |
| `apps.update` Write API | Added `VECINITA_CORS_ORIGINS` with plaintext value; auto-deploy ACTIVE |
| H1 post-CORS | ChatRAG `{"status":"ok","dependencies":{...}}` — all deps healthy |
| H4/H5 pytest | 4 pass, 1 waiver (Modal) |

**Note:** When using `do_apps.py sync-secrets`, provide ALL secret values in the shell env — DO's `apps.update` replaces the entire spec, and encrypted `EV[...]` values cannot be sent back. Use the pydo live-spec-update pattern (read spec → modify only target env → update) with plaintext values.

## Health Check

- ChatRAG dependencies: postgres ok, modal_embed ok, modal_llm ok
- No container crash loops on active backends

## Monitoring Baseline

- DO: 4 apps in `vecinita` project, `basic-xxs`, region `nyc`
- Postgres: `vecinita-staging` online
- Modal: scale-to-zero GPU/CPU apps on `vecinita` workspace

## Rollback

- Modal: `modal app stop vecinita-<app>`
- DO: redeploy previous deployment in App Platform or `do_apps.py deploy`
- Last known good (pre-deploy tag): `324bb50`

## Changelog

See [CHANGELOG.md](../CHANGELOG.md) (staging deploy slice).
