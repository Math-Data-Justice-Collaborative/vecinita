# Baseline: gateway live Schemathesis (pre-implementation)

**Date:** 2026-04-18

## Observed failures (historical)

- **`make test-schemathesis-cli`** against the public gateway reported **`not_a_server_error`** on Modal-backed scraper job operations under **`/api/v1/modal-jobs/scraper`** (submit, get, cancel paths), consistent with **500** responses when Modal attempted Postgres using an **internal** Render hostname (`dpg-*`) that does not resolve from Modal’s network.
- TraceCov / schema coverage for the live pass was **below 100%** on at least the **`responses`** dimension until OpenAPI `responses=` blocks are completed per **FR-006** (see `spec.md`).

## Target state

- Control-plane job rows and reads go through **Render** (`DATABASE_URL` / external URL as appropriate) when **`MODAL_SCRAPER_PERSIST_VIA_GATEWAY`** is enabled; Modal **enqueue-only** submit avoids opening Postgres in the Modal RPC path.
- OpenAPI lists **all** documented status codes for operations included in the Schemathesis live pass.
