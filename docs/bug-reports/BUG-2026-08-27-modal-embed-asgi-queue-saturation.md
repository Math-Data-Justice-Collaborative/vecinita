# BUG-2026-08-27 — Modal embed ASGI queue saturation (blocking .remote)

> Status: **open** (hotfix HF-272-275 / #275 #274 #272)  
> Feature: **F10** / **F2** ChatRAG ask + Modal embedding  
> Component: `infra/modal/embedding_app.py`, `rerank_app.py`, ChatRAG backend/FE

## Error description

Modal `vecinita-embedding` returns **HTTP 429** with pending input queue limit (2000).
ChatRAG on DigitalOcean returns **504 / no_healthy_upstream**. Users see cold-start
“assistant is starting up — try again” and corpus browse “Failed to load documents”.

## Error logs

```text
GET https://vecinita--vecinita-embedding-embedding-api.modal.run/health
modal-http: Function … reached pending input queue limit (2000) for workspace …
HTTP 429

GET https://vecinita-chat-rag-backend-jvqso.ondigitalocean.app/health
HTTP 504 no_healthy_upstream (503 UH)

GET https://vecinita--vecinita-llm-fastapi-app.modal.run/health → 200 ok
GET https://vecinita--vecinita-rerank-rerank-api.modal.run/health → timeout (60s)
```

## Investigation

| When (UTC) | Event |
|------------|-------|
| 2026-08-28 ~00:15 | Live probe: embed 429 queue full; ChatRAG UH; LLM health ok; rerank timeout |
| 2026-08-28 | Code review: `embedding_api` async routes call `service.embed_texts.remote()` (sync) |

### Root cause

Blocking `Function.remote()` inside **async** Starlette handlers holds each ASGI
worker until the class method returns. When `EmbeddingService` enter/load is slow or
failing, `/warm` + `/embed` pile up → Modal input queue hits 2000 → 429. ChatRAG ask
waits on embed (up to `VECINITA_REQUEST_TIMEOUT_S`) → DO marks instance unhealthy →
documents browse and ask both fail (cascade, not a separate Postgres bug).

Contributing: ChatRAG `_warm_modal_url` POSTs LLM `/warm` **without**
`X-Vecinita-Proxy-Key` (always 401); FE final error maps exhausted 503/TypeError to
“still starting” copy.

## Repro test

| Test | Path | Status |
|------|------|--------|
| ASGI no blocking `.remote()` | `tests/bugs/test_bug_2026_08_27_modal_asgi_blocking_remote.py` | red → green |
| Warm sends proxy key on LLM | `tests/unit/chat_rag/test_app_routes.py` | red → green |

## Fix

1. Use `await ….remote.aio(…)` (or `.spawn()` for fire-and-forget warm) in Modal ASGI.
2. Attach `VECINITA_MODAL_PROXY_KEY` on ChatRAG LLM warm.
3. Final ask failure copy → `askServerError` (ops-visible), not perpetual “starting up”.
4. Redeploy Modal embed/rerank/llm + DO ChatRAG to drain queues / clear UH.
