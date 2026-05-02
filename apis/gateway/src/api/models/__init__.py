"""
Unified API Gateway - Request/Response Models

Defines Pydantic schemas for Q&A, scraping, embeddings, and admin endpoints.
Enhanced with comprehensive Field descriptions, examples, and Pydantic v3 ConfigDict
for rich Swagger/OpenAPI documentation at /docs.
"""

# ruff: noqa: F403, I001

from .scrape import *
from .embed import *
from .ask import *
from .admin import *
from .gateway import *

# ============================================================================
# API ENDPOINT DOCUMENTATION & STATUS SUMMARY (Gateway v1)
# ============================================================================
"""
Unified API Gateway — OpenAPI and routing reference
=====================================================

All Pydantic models in this module feed FastAPI/OpenAPI for ``src.api.main``.

**Interactive docs (local default: port 8004)**

- Swagger UI: ``http://localhost:8004/api/v1/docs``
- OpenAPI JSON: ``http://localhost:8004/api/v1/docs/openapi.json`` (``/api/v1/openapi.json`` aliases the same document)
- Redoc: ``http://localhost:8004/api/v1/redoc``

**Versioned API base:** ``/api/v1/...`` (routers: ask, scrape, embed, documents).

**Compatibility routes (also listed in OpenAPI where applicable)**

- ``GET /health``, ``GET /config`` — same semantics as versioned health/config patterns.
- ``GET /integrations/status`` — operator integration matrix (also exposed under ``/api/v1/`` for probes).

**Q&A** — ``/api/v1/ask``, ``/api/v1/ask/stream``, ``/api/v1/ask/config``

**Scraping** — ``/api/v1/scrape`` and related job/history/stats/cleanup/reindex routes (see ``router_scrape.py``).

**Embeddings** — ``/api/v1/embed``, ``/embed/batch``, ``/embed/similarity``, ``/embed/config``.

**Public documents** — ``/api/v1/documents/*`` (overview, preview, tags, etc.).

**Authentication (when ``ENABLE_AUTH=true``)**

Protected routes expect ``Authorization: Bearer <api_key>`` (see ``AuthenticationMiddleware`` in ``middleware.py``).
Public prefixes include ``/api/v1/documents`` and selected discovery endpoints; see ``PUBLIC_ENDPOINTS``.

**Contract / Schemathesis**

- Offline gateway schema tests: ``tests/integration/test_api_schema_schemathesis.py`` (mocked upstreams).
- Offline agent schema tests: ``tests/integration/test_agent_api_schema_schemathesis.py``.
- From repo root: ``make test-schemathesis-gateway``, ``make test-schemathesis-agent``, ``make test-schemathesis``.

**cURL examples (gateway on 8004)**

  curl -sS 'http://localhost:8004/api/v1/ask/config'
  curl -sS 'http://localhost:8004/health'
  curl -sS 'http://localhost:8004/api/v1/docs/openapi.json' | head -c 200


BACKWARD COMPATIBILITY ALIASES
===============================

For migration/compatibility with existing code:

- ScrapeRequest → Use ScrapeStartRequest instead
- AskRequest → Use AskQuestionRequest instead
- AskResponse → Use AskQuestionResponse instead
- HealthCheck → Use HealthCheckResponse instead
- GatewayConfig → Use GatewayConfigResponse instead

Old names still resolve to new models but are deprecated in favor of the new explicit names.
"""
