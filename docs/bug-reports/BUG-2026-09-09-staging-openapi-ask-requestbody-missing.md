# BUG-2026-09-09-staging-openapi-ask-requestbody-missing

**Status:** Open (deploy lag)  
**Found by:** EV-staging-api-adversarial (2026-09-09)  
**Severity:** P1 (blocks Schemathesis / contract tools on staging)

## Error description

Staging ChatRAG `GET /openapi.json` omits `requestBody` for `POST /api/v1/ask`
(and `/api/v1/ask/stream`). Local `stage` branch already publishes AskRequest via
`openapi_extra` (TC-332 / #370), but the staging DigitalOcean ChatRAG app has not
picked up that image yet. Feedback similarly lacked requestBody until TC-333 fix
in this cycle.

## Error logs

```text
openapi /api/v1/ask requestBody False responses ['200']
openapi /api/v1/feedback requestBody False responses ['201']
```

(Preflight + mutation evidence under
`~/.cursor/workflow/.../EV-staging-api-adversarial/evidence/`.)

## Investigation

1. Confirmed local `create_app().openapi()` includes ask `requestBody`.
2. `origin/stage` contains `_ask_request_openapi_extra` (commit `4b757be4` / #370).
3. Live staging ChatRAG still serves OpenAPI without requestBody → **redeploy pending**.

## Repro test

- Unit (already green on branch): `tests/unit/chat_rag/test_openapi_ask_request_body.py`
- Live gate (red until redeploy): `tests/smoke/test_staging_openapi_request_bodies.py`

## Fix

1. Redeploy staging ChatRAG from current `stage` (includes AskRequest OpenAPI).
2. Merge + deploy this cycle’s Feedback OpenAPI + securitySchemes publishers.
3. Re-run TC-336 live smoke until green.
