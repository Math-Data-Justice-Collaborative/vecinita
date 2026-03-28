# Gateway API v1 Integration Points Matrix

This matrix maps each integration boundary to endpoint coverage and concrete test work.

| Integration Point ID | Integration Point | Endpoints | Matrix IDs | Test File Target | Status |
|---|---|---|---|---|---|
| IP-001 | Authentication middleware with auth proxy | Protected /api/v1 routes | GATEWAY-ASK-001, GATEWAY-SCRAPE-001, GATEWAY-EMBED-001, GATEWAY-ADMIN-* | tests/integration/test_gateway_auth.py + new gateway suites | planned |
| IP-002 | Rate limiting middleware | /api/v1/ask, /api/v1/scrape, /api/v1/embed, /api/v1/admin | GATEWAY-ASK-001, GATEWAY-EMBED-001..003, GATEWAY-SCRAPE-001 | tests/integration/test_gateway_auth.py + new rate tests | planned |
| IP-003 | Agent service proxy | /api/v1/ask, /api/v1/ask/stream, /api/v1/admin/models/config | GATEWAY-ASK-001..003, GATEWAY-ADMIN-012..013 | tests/integration/test_streaming.py + new ask suite | planned |
| IP-004 | Embedding service proxy | /api/v1/embed*, /api/v1/admin/models/config | GATEWAY-EMBED-001..005, GATEWAY-ADMIN-012..013 | new embed integration suite | planned |
| IP-005 | Scraper pipeline and uploader | /api/v1/scrape*, /api/v1/admin/sources* | GATEWAY-SCRAPE-001..007, GATEWAY-ADMIN-014..015 | existing and new scrape/admin suites | planned |
| IP-006 | Modal reindex trigger | /api/v1/scrape/reindex | GATEWAY-SCRAPE-005 | tests/integration/test_modal_reindex_trigger.py | planned |
| IP-007 | Admin JWT role verification | /api/v1/admin* + admin-only non-admin routes | GATEWAY-ADMIN-001..022, GATEWAY-EMBED-005, GATEWAY-SCRAPE-004..005 | test_gateway_auth + new admin suite | planned |
| IP-008 | Vector store operations | /api/v1/admin/documents*, /api/v1/documents* | GATEWAY-ADMIN-003..004,018 and GATEWAY-DOCS-* | existing chroma flow + new docs suite | planned |
| IP-009 | Database metadata operations | /api/v1/admin/sources*, /api/v1/admin/tags, /api/v1/documents* | GATEWAY-ADMIN-007..017 and GATEWAY-DOCS-* | admin tag flow + new docs suite | planned |
| IP-010 | File upload and storage URL resolution | /api/v1/admin/upload, /api/v1/documents/download-url | GATEWAY-ADMIN-022, GATEWAY-DOCS-003 | new upload/docs tests | planned |

## Completion Rules

- `planned`: test cases defined, not yet committed.
- `implemented`: tests committed and mapped to matrix IDs.
- `passing`: tests are green in CI workflows.

## Required Gate

All rows must be at least `implemented` before releasing a Gateway API v1 contract change.
