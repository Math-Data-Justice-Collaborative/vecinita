# E2E and Integration Tests

Independent test environment for testing backend ↔ frontend interactions, completely separate from backend unit tests.

## Quick Start

```bash
# Terminal 1: Backend
cd backend
uv sync
uv run uvicorn src.agent.main:app --reload

# Terminal 2: Frontend  
cd frontend
npm install
npm run dev

# Terminal 3: Tests (from root)
cd tests
uv sync
uv run pytest -v
```

## Structure

```
tests/
├── conftest.py                  ← Root pytest config and fixtures
├── pyproject.toml               ← Independent project dependencies
├── .env.example                 ← Configuration template
├── README.md                    ← This file
│
├── src/
│   └── utils.py                 ← APIClient for HTTP testing
│
├── integration/
│   ├── conftest.py
│   ├── test_api.py              ← Backend API endpoint tests
│   └── test_agent.py            ← LangGraph agent tests
│
├── e2e/
│   ├── conftest.py
│   └── test_sources.py          ← End-to-end source attribution tests
│
└── docs/
    ├── README.md                ← Full documentation
    └── README_QUICK_START.txt   ← Quick reference
```

## Test Types

| Type | Location | Marker | Requirements | Speed |
|------|----------|--------|-------------|-------|
| **Integration** | `integration/` | `@pytest.mark.integration` | Backend running | 1-5s |
| **E2E** | `e2e/` | `@pytest.mark.e2e` | Backend + Frontend | 5-30s |
| **Unit** | `../backend/tests/` | None | Nothing | <1s |

## Running Tests

```bash
# All tests (backend-enabled)
uv run pytest -v

# Discover tests without running
uv run pytest --collect-only -q

# Integration tests only
uv run pytest -v -m integration

# E2E tests only  
uv run pytest -v -m e2e

# Skip backend-dependent tests
SKIP_INTEGRATION=true SKIP_E2E=true uv run pytest -v

# With coverage
uv run pytest -v --cov=.
```

## Expected Behavior Without Backend

When the backend service is **not running**:
- ✅ 8 tests are **skipped** gracefully
- ✅ 3 tests **pass** (no backend dependency)
- ❌ 3 tests **fail** (require backend)

This is normal! Integration tests only pass when their services are running.

## Configuration

### Environment Variables

Create `.env` from `.env.example`:

```bash
cp .env.example .env
```

Variables:
- `BACKEND_URL` - Backend API URL (default: http://localhost:8004 for Gateway, 8000 for Agent)
- `FRONTEND_URL` - Frontend dev server URL (default: http://localhost:5173)
- `SKIP_E2E` - Skip E2E tests (default: false)
- `SKIP_INTEGRATION` - Skip integration tests (default: false)
- `API_TIMEOUT` - Request timeout in seconds (default: 10)

## API v1 Testing (Updated for Gateway)

The tests now target the **API Gateway** service with v1 versioning:

### Default Backend URL Changed
- **NEW:** `http://localhost:8004` (API Gateway with `/api/v1/*` endpoints)
- **OLD:** `http://localhost:8000` (Agent service - still used by backend/tests/)

### Tested Endpoints
```
Root & Documentation:
  GET /                        → Service info (JSON) or Frontend (HTML)
  GET /health                  → Health check (backward compatible)
  GET /api/v1/docs             → Swagger UI
  GET /api/v1/docs/openapi.json → OpenAPI schema (GET /api/v1/openapi.json aliases)

Q&A Endpoints:
  GET /api/v1/ask?question=... → Ask question
  GET /api/v1/ask/stream       → Streaming response
  GET /api/v1/ask/config       → Configuration

Admin Endpoints:
  GET /api/v1/admin/health     → Health status
  GET /api/v1/admin/config     → Admin configuration
  GET /api/v1/admin/stats      → Statistics

Scraping Endpoints:
  POST /api/v1/scrape          → Start scraping job
  GET /api/v1/scrape/{job_id}  → Job status
  GET /api/v1/scrape/history   → Job history
  GET /api/v1/scrape/stats     → Statistics

Embedding Endpoints:
  GET /api/v1/embed/config     → Embedding configuration
```

### Running Gateway for Tests
```bash
# Start API Gateway with demo mode
cd backend
DEMO_MODE=true python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8004

# Run tests against gateway
cd tests
pytest integration/ -v
```

### Test Files
- **test_api.py** - Core API endpoint tests (updated for v1)
- **test_api_v1_features.py** - New tests for API v1 features:
  - Versioning structure
  - Documentation endpoints
  - Response format validation
  - Error handling

Modal reindex trigger coverage is validated in backend test suites:
- `backend/tests/test_api/test_gateway_router_scrape.py` (unit)
- `backend/tests/integration/test_modal_reindex_trigger.py` (integration)
- `backend/tests/e2e/test_reindex_flow.py` (e2e)

### Response Format (API v1)
```json
{
  "question": "What is Vecinita?",
  "answer": "...",
  "sources": [
    {
      "url": "https://...",
      "title": "...",
      "chunk_id": "...",
      "relevance": 0.95
    }
  ],
  "language": "en",
  "model": "demo-mode",
  "response_time_ms": 123,
  "token_usage": {
    "prompt_tokens": 0,
    "completion_tokens": 0,
    "total_tokens": 0
  }
}
```
- `FRONTEND_URL` - Frontend URL (default: http://localhost:5173)
- `SKIP_INTEGRATION` - Skip integration tests (default: false)
- `SKIP_E2E` - Skip E2E tests (default: false)
- `API_TIMEOUT` - HTTP request timeout in seconds (default: 10)

### Backend Integration Testing

Some tests require a running backend with:
- PostgreSQL database configured
- Groq API key (`GROQ_API_KEY`)
- Valid URLs in data configuration

## Import Pattern

Tests use **HTTP client** (`APIClient`) instead of direct imports for true independence:

```python
from utils import APIClient

def test_ask_endpoint(backend_url):
    api = APIClient(backend_url)
    response = api.ask(query="What is Vecinita?")
    assert "answer" in response
```

This ensures the tests are **completely separate** from the backend code.

## Documentation

For more details, see [docs/README.md](docs/README.md)
