# BUG-2026-08-05 — ChatRAG ask blocks health (DO 504 UH)

> Status: **fixed** (local; pending deploy) — S027-D51 / S027-D52  
> Feature: **F2** / H3 smoke (also blocks F70–F71 live cutover)  
> Component: `apps/chat-rag-backend` on DO `basic-xxs` (1 instance)

## Error description

During staging H3 (`POST /api/v1/ask`), ChatRAG becomes unreachable: DigitalOcean returns
**504** with `x-do-failure-code: UH` / `no_healthy_upstream`. `/health` was **200** with
`modal_embed`/`modal_llm`/`postgres` ok immediately before the ask. After redeploy, health
recovers until the next ask.

## Error logs

```text
# H1 (pre-ask) — PASS
GET /health → 200 {"status":"ok","dependencies":{"postgres":"ok","modal_embed":"ok","modal_llm":"ok"}}

# H3
POST /api/v1/ask  (curl 180s) → 0 bytes; then:
HTTP/2 504
x-do-failure-code: UH
x-do-failure-msg: no_healthy_upstream

# Concurrent H4 OPTIONS during outage → ReadTimeout / 504
# After doctl apps create-deployment → /health 200 again
# Safe OPTIONS when healthy → 200 + Access-Control-Allow-Origin correct
```

| Field | Value |
|-------|--------|
| App | `vecinita-chat-rag-backend` (`083e1cb9-…`) |
| Instance | `basic-xxs` × 1 |
| Run command | `uvicorn …:create_app --factory` (default 1 worker) |
| Commit deployed | `de1355c` (CD) + manual redeploys |

## Investigation

### Timeline

| When (UTC) | Event |
|------------|-------|
| 2026-08-05 ~20:07 | DO CD ACTIVE @ `de1355c` |
| ~21:31 | H1 PASS; H3 ask started; H4 pytest timeouts |
| ~21:35 | ChatRAG 504 UH |
| ~21:40 | Manual redeploy → health ok |
| ~21:42 | Second H3 ask (180s) → again 504 UH |
| ~21:45 | Second redeploy → health ok; OPTIONS H4 PASS |
| ~21:50 | S027-D51 investigate+fix |
| ~21:54 | S027-D52 root cause confirmed; `asyncio.to_thread` applied |

### Hypotheses

| # | Hypothesis | Status |
|---|------------|--------|
| H1 | `async def ask` calls sync `ChatRagService.ask` (httpx to Modal) on the event loop → uvicorn cannot accept/process DO `/health` probes → UH | **Confirmed** |
| H2 | Modal LLM cold start > DO gateway ~60s alone (BUG-2026-05-22) | Contributing latency; not the UH mechanism |
| H3 | OOM kill on `basic-xxs` during ask | Not evidenced |
| H4 | Health probe itself overloaded | Unlikely alone |

### Root cause

**Confirmed (S027-D52):** Event-loop blocking from sync ask/stream setup inside `async`
routes on a single uvicorn worker (`basic-xxs`), so App Platform health checks fail and the
LB reports `no_healthy_upstream`.

## Repro test

| Test | Path | Status |
|------|------|--------|
| Event-loop ticker during slow ask | `tests/bugs/test_bug_2026_08_05_chatrag_ask_blocks_health.py` | red → **green** |

## Fix

| File | Change |
|------|--------|
| `apps/chat-rag-backend/vecinita_chat_rag_backend/app.py` | `await asyncio.to_thread(get_service().ask, body)` on `POST /api/v1/ask`; `await asyncio.to_thread(service.stream_ask, body)` for stream setup |

## Interview record

| Gate | Answer |
|------|--------|
| S027-D51 | Option 1 — investigate and fix |
| S027-D52 | Option 1 — confirm RC; apply `to_thread` |

## Prevention & countermeasures

Pending post-deploy: consider rule “no sync I/O in `async def` FastAPI routes” + optional
warm before H3. Cold-start gateway timeout remains covered by BUG-2026-05-22.
