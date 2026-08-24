# BUG-2026-08-24 — vecinita-rerank ASGI crash (missing starlette)

## Error description

Modal `vecinita-rerank` HTTP endpoint never returns 200 on `/health` or `/score`.
External probes see HTTP 303 retry loops (~150s) then staging ChatRAG `/api/v1/ask`
504s when `VECINITA_RAG_RERANK_CE=true`.

## Error logs

```
ModuleNotFoundError: No module named 'starlette'
  File "/root/rerank_app.py", line 76, in rerank_api
    from starlette.applications import Starlette
Function rerank_app.rerank_api is crash-looping: containers are repeatedly failing to start.
```

## Investigation

- EV-029 M5 staging cutover: rerank deployed, DO secrets synced, ChatRAG `/health` ok.
- Direct curl to `vecinita--vecinita-rerank-rerank-api.modal.run` never warmed — 303 only.
- `uv run modal app logs vecinita-rerank` shows ASGI function `rerank_api` missing `starlette`
  in `pip_install`; GPU class image has sentence-transformers only.
- `llm_app.py` already pins `starlette>=0.37,<1` for its ASGI layer.

## Root cause

1. `infra/modal/rerank_app.py` `pip_install` omitted `starlette` while `rerank_api` imports it.
2. `RerankClient` forwarded `VECINITA_MODAL_PROXY_KEY` as `Modal-Proxy-Authorization`;
   open rerank HTTP returns **400** (`prohibited modal header`), surfacing as ChatRAG **503**.

## Repro test

- `tests/bugs/test_bug_2026_08_24_rerank_missing_starlette.py` — image includes starlette.
- `tests/unit/rerank_client/test_client.py` — no proxy header on `/score`.

## Fix

1. Add `starlette>=0.37,<1` to rerank Modal image; redeploy `vecinita-rerank`.
2. Stop sending proxy auth from `RerankClient`; redeploy ChatRAG backend.

## Resolution (2026-08-24)

- Hotfix PR #261 merged; ChatRAG redeployed via CD.
- Staging `POST /api/v1/ask` PASS (H3 smoke).
- Status: **resolved**
