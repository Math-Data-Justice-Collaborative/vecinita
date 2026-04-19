# Quickstart: working with Render-owned DB + Modal payloads

## Render (gateway / agent)

- Ensure **only** Render services have `DATABASE_URL` (or split read/write URLs) with a hostname
  reachable from **Render** containers (per Render Postgres docs: **external** URL when calling
  from outside Render’s private network).
- Remove `MODAL_DATABASE_URL` (or equivalent) from **Modal** secrets once scraper/model/embed no
  longer open DB—keep it **only** if a Render-hosted process still needs it (should not be Modal).

## Modal (model / embedding / scraper)

- Functions return **JSON-serializable** results only; **no** `psycopg`, **no** `DATABASE_URL` read.  
- Use smaller batches if gateway HTTP timeout is tight.

## Local dev

- Use existing gateway mocks (`test_api_schema_schemathesis` pattern) to simulate Modal returns.  
- Run `make test-schemathesis-gateway` before `make test-schemathesis-cli`.

## Verify

1. `make test-schemathesis-cli` against staging with TraceCov gate.  
2. Modal dashboard logs show **no** Postgres connection attempts from scraper/model/embed functions.
