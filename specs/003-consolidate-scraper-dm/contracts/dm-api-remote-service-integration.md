# Contract: Data-management-api → remote scraper, embedding, model

**Status**: Draft (feature `003-consolidate-scraper-dm`)  
**Normative spec**: [../spec.md](../spec.md) clarifications **B** (remote APIs only).

## Purpose

Define how the **data-management-api** backend obtains scraper, embedding, and model behavior **after**
nested submodules are removed. This is a **service-to-service** contract, not the public gateway
OpenAPI.

## Configuration (environment)

| Variable | Required | Description |
|----------|----------|-------------|
| `SCRAPER_SERVICE_BASE_URL` | yes | Origin for canonical scraper HTTP API (trailing slash normalized in client) |
| `EMBEDDING_SERVICE_BASE_URL` | yes | Origin for embedding HTTP API |
| `MODEL_SERVICE_BASE_URL` | yes | Origin for model HTTP API |
| `*_SERVICE_TIMEOUT_SECONDS` | recommended | Per-upstream timeouts; default documented in implementation |
| Auth secrets | per env | Bearer token or API key header names agreed with each deployable |

**Failure modes**:

- Missing URL at startup: fail fast in production, or explicit **503** with safe message for health
  surfaces (implementation choice documented in tasks).  
- Upstream **5xx** / network error: DM API maps to **502** / **503** with **FR-002**-safe body and
  **correlation_id**; never fall back to a local duplicate implementation.

## HTTP expectations

- **TLS**: HTTPS in staging/production unless local dev explicitly allows HTTP.  
- **Versioning**: Paths or headers versioned consistently with each sibling service’s OpenAPI.  
- **Idempotency**: Where upstream supports it, respect idempotency keys for create operations.

## Observability

- Propagate **correlation_id** (or W3C `traceparent` if adopted) on every outbound request (**FR-006**).  
- Log upstream status and latency at **info**; never log full secrets or raw DSNs.

## Parity obligation

Behavior of DM API endpoints that previously called in-process submodule code **MUST** match the
**parity suite** (see [../quickstart.md](../quickstart.md)) within documented tolerances before
submodules are deleted from the default branch.
