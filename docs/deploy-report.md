# Deploy Report

> Date: 2026-05-20 (last re-validated 2026-05-20)
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

H3 returned a valid `answer` + `language: en` with fixture `sources` on re-validate (~1.7s warm; first cold run may 504 until Modal LLM scales up).

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

**Note:** Run `staging_smoke.sh` only after DO backends are ACTIVE and optionally warm LLM once; immediate H3 after redeploy can 504.

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
