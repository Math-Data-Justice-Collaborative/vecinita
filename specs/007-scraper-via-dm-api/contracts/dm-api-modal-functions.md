# Contract: Data-management API ↔ Modal deployed functions

## Purpose

Define the **server-side** integration contract when `apis/data-management-api` calls Modal-deployed apps **without** using public Modal FastAPI URLs for scraper, embedding, or model ingest paths.

## Modal SDK surface (caller side)

- Resolution: `modal.Function.from_name(app_name, function_name, environment_name=optional)`.
- Invocation: `.remote(**kwargs)` for synchronous RPC-style calls; `.spawn(**kwargs)` when work is asynchronous, followed by `modal.FunctionCall.from_id(id).get(timeout=...)` where the DM API must return poll handles to its own HTTP clients.

## Scraper app (`vecinita-scraper` defaults)

| Logical operation | Default function name | Payload / result |
|-------------------|----------------------|------------------|
| Submit job | `modal_scrape_job_submit` | Dict matching `ScrapeJobRequest` / queue payload; result envelope with `ok`, `job_id`, optional `modal_function_call_id`. |
| Get job | `modal_scrape_job_get` | `job_id: str`; envelope with status fields. |
| List jobs | `modal_scrape_job_list` | `user_id`, `limit`; list envelope. |
| Cancel job | `modal_scrape_job_cancel` | `job_id`; envelope. |

**Errors**: Scraper RPC uses structured `_rpc_err` codes (`validation_error`, `database_error`, `internal_error`); DM API MUST map these to HTTP status codes documented on DM OpenAPI without leaking stack traces.

## Embedding app (`vecinita-embedding` defaults)

| Operation | Default function | Notes |
|-----------|------------------|--------|
| Single embed | `embed_query` | Text in → vector metadata out per existing schema. |
| Batch embed | `embed_batch` | List in → batch out. |

## Model app (`vecinita-model` defaults)

| Operation | Default function | Notes |
|-----------|------------------|--------|
| Chat completion | `chat_completion` | `model`, `messages`, `temperature` — only when DM ingest pipeline requires LLM steps. |

## Versioning

Function renames or app splits require **coordinated deploy** of Modal apps + DM API env configuration; document in release notes.
