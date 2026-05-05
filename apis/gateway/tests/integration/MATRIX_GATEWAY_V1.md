# Gateway API v1 Integration Matrix

This matrix is the source of truth for endpoint-level integration coverage for the Gateway API v1 surface.

## Status Legend

- `planned`: scenario is required and tracked
- `contract-covered`: integration-point contract tests explicitly cover the route contract
- `acceptance-covered`: route-level acceptance tests cover success/failure scenarios
- `schema-covered`: Schemathesis / OpenAPI conformance currently exercises the route
- `ci-passing`: relevant tests are executed in CI

## Endpoint Coverage Matrix

| Matrix ID | Method | Path | Auth Mode | Integration Points | Required Scenario Set | Current Status |
|---|---|---|---|---|---|---|
| GATEWAY-ASK-001 | GET | /api/v1/ask | API Key | Auth Proxy, Rate Limiter, Agent Service, Vector Store | Success, Auth Failure, Validation Failure, Upstream Failure, Rate Limit | contract-covered, acceptance-covered, schema-covered |
| GATEWAY-ASK-002 | GET | /api/v1/ask/stream | API Key | Auth Proxy, Rate Limiter, Agent Service (SSE) | SSE Success, Auth Failure, Stream Failure, Upstream Failure, Rate Limit | contract-covered, acceptance-covered |
| GATEWAY-ASK-003 | GET | /api/v1/ask/config | Public | Agent Service | Success, Fallback/Degraded Config | contract-covered, acceptance-covered, schema-covered |
| GATEWAY-SCRAPE-001 | POST | /api/v1/scrape | API Key | Auth Proxy, Rate Limiter, Scraper Pipeline, DB Uploader | Success, Auth Failure, Payload Validation, Scraper Failure | planned |
| GATEWAY-SCRAPE-002 | GET | /api/v1/scrape/history | API Key | Auth Proxy, Scraper Job Manager | Success, Auth Failure, Pagination Validation | planned |
| GATEWAY-SCRAPE-003 | GET | /api/v1/scrape/stats | API Key | Auth Proxy, Scraper Job Manager | Success, Auth Failure | planned |
| GATEWAY-SCRAPE-004 | POST | /api/v1/scrape/cleanup | Admin JWT | Admin JWT Verify, Job Manager | Admin Success, Non-admin Rejection, Validation | planned |
| GATEWAY-SCRAPE-005 | POST | /api/v1/scrape/reindex | Admin JWT | Admin JWT Verify, Modal Reindex Service | Admin Success, Non-admin Rejection, Upstream Failure | contract-covered |
| GATEWAY-SCRAPE-006 | GET | /api/v1/scrape/{job_id} | API Key | Auth Proxy, Scraper Job Manager | Success, Not Found, Auth Failure | planned |
| GATEWAY-SCRAPE-007 | POST | /api/v1/scrape/{job_id}/cancel | API Key | Auth Proxy, Scraper Job Manager | Success, Not Found, Auth Failure | planned |
| GATEWAY-EMBED-001 | POST | /api/v1/embed | API Key | Auth Proxy, Rate Limiter, Embedding Service | Success, Auth Failure, Validation Failure, Upstream Failure, Rate Limit | contract-covered, schema-covered |
| GATEWAY-EMBED-002 | POST | /api/v1/embed/batch | API Key | Auth Proxy, Rate Limiter, Embedding Service | Success, Auth Failure, Validation Failure, Upstream Failure, Rate Limit | contract-covered, schema-covered |
| GATEWAY-EMBED-003 | POST | /api/v1/embed/similarity | API Key | Auth Proxy, Rate Limiter, Embedding Service | Success, Auth Failure, Validation Failure, Upstream Failure, Rate Limit | contract-covered, schema-covered |
| GATEWAY-EMBED-004 | GET | /api/v1/embed/config | Public | Embedding Service | Success, Service Failure Mapping | schema-covered |
| GATEWAY-EMBED-005 | POST | /api/v1/embed/config | Admin JWT | Admin JWT Verify, Embedding Service | Admin Success, Non-admin Rejection, Validation Failure | schema-covered |
| GATEWAY-ADMIN-001 | GET | /api/v1/admin/health | Admin JWT | Admin JWT Verify, Agent Service, Embedding Service, DB Connectivity | Admin Success, Non-admin Rejection, Dependency Failure | planned |
| GATEWAY-ADMIN-002 | GET | /api/v1/admin/stats | Admin JWT | Admin JWT Verify, Vector Store, DB | Admin Success, Non-admin Rejection | planned |
| GATEWAY-ADMIN-003 | GET | /api/v1/admin/documents | Admin JWT | Admin JWT Verify, Vector Store, DB | Admin Success, Non-admin Rejection, Validation | planned |
| GATEWAY-ADMIN-004 | DELETE | /api/v1/admin/documents/{chunk_id} | Admin JWT | Admin JWT Verify, Vector Store, DB | Admin Success, Non-admin Rejection, Not Found | planned |
| GATEWAY-ADMIN-005 | POST | /api/v1/admin/database/clean | Admin JWT + Confirmation | Admin JWT Verify, DB | Admin Success, Non-admin Rejection, Missing Confirmation | planned |
| GATEWAY-ADMIN-006 | GET | /api/v1/admin/database/clean-request | Admin JWT | Admin JWT Verify, Token Store | Admin Success, Non-admin Rejection | planned |
| GATEWAY-ADMIN-007 | GET | /api/v1/admin/sources | Admin JWT | Admin JWT Verify, DB | Admin Success, Non-admin Rejection | planned |
| GATEWAY-ADMIN-008 | POST | /api/v1/admin/sources/validate | Admin JWT | Admin JWT Verify, External URL Access | Admin Success, Non-admin Rejection, Validation Failure | planned |
| GATEWAY-ADMIN-009 | GET | /api/v1/admin/config | Admin JWT | Admin JWT Verify | Admin Success, Non-admin Rejection | planned |
| GATEWAY-ADMIN-010 | POST | /api/v1/admin/config | Admin JWT | Admin JWT Verify | Admin Success, Non-admin Rejection, Validation Failure | planned |
| GATEWAY-ADMIN-011 | GET | /api/v1/admin/diagnostics/schema | Admin JWT | Admin JWT Verify, DB Schema Diagnostics | Admin Success, Non-admin Rejection | planned |
| GATEWAY-ADMIN-012 | GET | /api/v1/admin/models/config | Admin JWT | Admin JWT Verify, Agent Service, Embedding Service | Admin Success, Non-admin Rejection | planned |
| GATEWAY-ADMIN-013 | POST | /api/v1/admin/models/config | Admin JWT | Admin JWT Verify, Agent Service, Embedding Service | Admin Success, Non-admin Rejection, Validation Failure | planned |
| GATEWAY-ADMIN-014 | POST | /api/v1/admin/sources | Admin JWT | Admin JWT Verify, Scraper Pipeline, DB | Admin Success, Non-admin Rejection, Validation Failure, Dependency Failure | planned |
| GATEWAY-ADMIN-015 | POST | /api/v1/admin/sources/batch | Admin JWT | Admin JWT Verify, Scraper Pipeline, DB | Admin Success, Non-admin Rejection, Validation Failure | planned |
| GATEWAY-ADMIN-016 | PATCH | /api/v1/admin/sources/tags | Admin JWT | Admin JWT Verify, DB | Admin Success, Non-admin Rejection, Validation Failure | planned |
| GATEWAY-ADMIN-017 | GET | /api/v1/admin/tags | Admin JWT | Admin JWT Verify, DB | Admin Success, Non-admin Rejection | planned |
| GATEWAY-ADMIN-018 | DELETE | /api/v1/admin/sources | Admin JWT | Admin JWT Verify, DB, Vector Store | Admin Success, Non-admin Rejection, Not Found | planned |
| GATEWAY-ADMIN-019 | GET | /api/v1/admin/queue | Admin JWT | Admin JWT Verify, Queue Backend | Admin Success, Non-admin Rejection | planned |
| GATEWAY-ADMIN-020 | GET | /api/v1/admin/queue/status-summary | Admin JWT | Admin JWT Verify, Queue Backend | Admin Success, Non-admin Rejection | planned |
| GATEWAY-ADMIN-021 | GET | /api/v1/admin/stats/chunk-domains | Admin JWT | Admin JWT Verify, DB | Admin Success, Non-admin Rejection | planned |
| GATEWAY-ADMIN-022 | POST | /api/v1/admin/upload | Admin JWT | Admin JWT Verify, File Parser, Storage, DB | Admin Success, Non-admin Rejection, Validation Failure, Storage Failure | planned |
| GATEWAY-DOCS-001 | GET | /api/v1/documents/overview | Public | DB, Vector Store | Success, Fallback on Missing DB | contract-covered, schema-covered |
| GATEWAY-DOCS-002 | GET | /api/v1/documents/preview | Public | DB, Vector Store | Success, Validation Failure, Not Found | planned |
| GATEWAY-DOCS-003 | GET | /api/v1/documents/download-url | Public | Storage URL Resolver | Success, Validation Failure | contract-covered |
| GATEWAY-DOCS-004 | GET | /api/v1/documents/chunk-statistics | Public | DB, Vector Store | Success, Fallback on Missing DB | planned |
| GATEWAY-DOCS-005 | GET | /api/v1/documents/tags | Public | DB | Success, Fallback on Missing DB | planned |

## Notes

- This file is validated by [backend/tests/integration/test_gateway_v1_matrix_coverage.py](test_gateway_v1_matrix_coverage.py).
- Add new matrix rows before adding new Gateway API v1 endpoints.
- Move status from `planned` -> `contract-covered` -> `acceptance-covered` / `schema-covered` -> `ci-passing` as tests land and are promoted.
