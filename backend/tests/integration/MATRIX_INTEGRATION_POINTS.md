# Gateway API v1 Integration Points Matrix

This matrix maps each integration boundary to concrete test evidence and the next missing layer of coverage.

## Status Legend

- `planned`: tracked only, no committed evidence yet.
- `contract-covered`: explicit integration-point contract tests exist.
- `acceptance-covered`: route-level acceptance tests exist for primary scenarios.
- `schema-covered`: Schemathesis / OpenAPI conformance currently exercises the stable surface.
- `ci-passing`: the relevant suites are executed in CI and expected to gate changes.

| Integration Point ID | Integration Point | Endpoints | Matrix IDs | Contract Coverage | Acceptance Coverage | Schema Coverage | Evidence | Next Focus |
|---|---|---|---|---|---|---|---|---|
| IP-001 | Authentication middleware with auth routing | Protected /api/v1 routes | GATEWAY-ASK-001, GATEWAY-SCRAPE-001, GATEWAY-EMBED-001, GATEWAY-ADMIN-* | contract-covered | partial | planned | `tests/integration/test_gateway_auth.py`, `tests/integration/test_gateway_ask_acceptance.py` | Add embed and admin acceptance suites |
| IP-002 | Rate limiting middleware | /api/v1/ask, /api/v1/scrape, /api/v1/embed, /api/v1/admin | GATEWAY-ASK-001, GATEWAY-EMBED-001..003, GATEWAY-SCRAPE-001 | contract-covered | partial | planned | `tests/integration/test_gateway_auth.py`, `tests/integration/test_gateway_ask_acceptance.py` | Add embed and scrape 429 acceptance checks |
| IP-003 | Agent service routing | /api/v1/ask, /api/v1/ask/stream, /api/v1/admin/models/config | GATEWAY-ASK-001..003, GATEWAY-ADMIN-012..013 | contract-covered | acceptance-covered | schema-covered | `tests/integration/test_service_integration_points_contract*.py`, `tests/integration/test_streaming.py`, `tests/integration/test_api_schema_schemathesis.py`, `tests/integration/test_gateway_ask_acceptance.py` | Add admin models config acceptance suite |
| IP-004 | Embedding service routing | /api/v1/embed*, /api/v1/admin/models/config | GATEWAY-EMBED-001..005, GATEWAY-ADMIN-012..013 | contract-covered | planned | schema-covered | `tests/integration/test_service_integration_points_contract*.py`, `tests/integration/test_api_schema_schemathesis.py` | Add embed acceptance suite |
| IP-005 | Scraper pipeline and uploader | /api/v1/scrape*, /api/v1/admin/sources* | GATEWAY-SCRAPE-001..007, GATEWAY-ADMIN-014..015 | contract-covered | partial | planned | `tests/integration/test_service_integration_points_contract*.py`, `tests/integration/test_modal_reindex_trigger.py` | Add scrape lifecycle acceptance suite |
| IP-006 | Modal reindex trigger | /api/v1/scrape/reindex | GATEWAY-SCRAPE-005 | contract-covered | partial | planned | `tests/integration/test_modal_reindex_trigger.py`, `tests/integration/test_service_integration_points_contract*.py` | Add admin-auth and upstream-failure acceptance coverage |
| IP-007 | Admin JWT role verification | /api/v1/admin* + admin-only non-admin routes | GATEWAY-ADMIN-001..022, GATEWAY-EMBED-005, GATEWAY-SCRAPE-004..005 | planned | planned | planned | tracked in matrix only | Add dedicated admin auth acceptance suite |
| IP-008 | Vector store operations | /api/v1/admin/documents*, /api/v1/documents* | GATEWAY-ADMIN-003..004,018 and GATEWAY-DOCS-* | contract-covered | planned | partial | `tests/integration/test_service_integration_points_contract*.py`, `tests/integration/test_api_schema_schemathesis.py` | Add public documents acceptance suite |
| IP-009 | Database metadata operations | /api/v1/admin/sources*, /api/v1/admin/tags, /api/v1/documents* | GATEWAY-ADMIN-007..017 and GATEWAY-DOCS-* | contract-covered | planned | partial | `tests/integration/test_service_integration_points_contract*.py`, `tests/integration/test_api_schema_schemathesis.py` | Add admin sources / tags acceptance suite |
| IP-010 | File upload and storage URL resolution | /api/v1/admin/upload, /api/v1/documents/download-url | GATEWAY-ADMIN-022, GATEWAY-DOCS-003 | contract-covered | planned | planned | `tests/integration/test_service_integration_points_contract*.py` | Add upload + download-url acceptance suite |

## Required Gate

Every integration point should reach at least `contract-covered` before a Gateway v1 contract change merges, and high-risk public routes should progress to `acceptance-covered` plus `schema-covered`.
