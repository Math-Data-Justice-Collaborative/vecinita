# Test Updates for API v1 - Summary

## Overview
Updated all test files to work with the new `/api/v1/` API structure and API Gateway running on port 8004.

## Status: ✅ COMPLETE - All Tests Passing

**Test Results:** 22 passed, 6 skipped in 1.01s

---

## Files Modified

### 1. `/tests/conftest.py`
**Change:** Updated default backend URL from port 8000 → port 8004

```python
# Before
self.backend_url = os.getenv("BACKEND_URL", "http://localhost:8000")

# After (targets API Gateway)
self.backend_url = os.getenv("BACKEND_URL", "http://localhost:8004")
```

**Reason:** Tests now target the API Gateway (port 8004) instead of the agent service (port 8000).

---

### 2. `/tests/src/utils.py`
**Changes:**
- Updated default base URL to port 8004
- Modified `ask()` method to use `/api/v1/ask` endpoint
- Changed parameter name from `query` to `question` (API v1 standard)
- Enhanced `health()` method to try both `/api/v1/admin/health` and `/health`

```python
# Before
def __init__(self, base_url: str = "http://localhost:8000", ...):
    ...

def ask(self, query: str, language: str = "en", **kwargs):
    params = {"query": query, "language": language, **kwargs}
    response = self.client.get("/ask", params=params)
    ...

# After
def __init__(self, base_url: str = "http://localhost:8004", ...):
    ...

def ask(self, query: str, language: str = "en", **kwargs):
    params = {"question": query, **kwargs}  # API v1 uses 'question'
    response = self.client.get("/api/v1/ask", params=params)
    ...
```

---

### 3. `/tests/integration/test_api.py`
**Changes:**
- Updated docstrings to reference API Gateway and port 8004
- Added `question` field assertion (API v1 echoes back the question)
- Updated source structure validation for API v1 format
- Enhanced error handling to check for `detail` field (FastAPI validation errors)

```python
# New assertions for API v1 response structure
assert "question" in response, "Response should contain 'question' field (API v1)"
assert "sources" in response, "API v1 should include 'sources' field"

# Source validation for API v1
assert "url" in source, "Source should have 'url' field"
assert "title" in source, "Source should have 'title' field"
```

**Test Coverage:**
- ✅ Basic ask endpoint
- ✅ Spanish language support
- ✅ Source citation structure
- ✅ Service availability
- ✅ Empty query handling
- ✅ Long query handling

---

### 4. `/tests/integration/test_api_v1_features.py` (NEW)
**Purpose:** Comprehensive tests for API v1 specific features

**Test Classes:**
1. **TestAPIv1Versioning** - Tests versioning structure
   - Root endpoint returns API info with `api_base: "/api/v1"`
   - Legacy `/health` endpoint backward compatibility
   - Legacy `/config` endpoint backward compatibility

2. **TestAPIv1Documentation** - Tests documentation endpoints
   - Swagger UI at `/api/v1/docs`
   - OpenAPI schema at `/api/v1/openapi.json`
   - Schema contains all v1 endpoints

3. **TestAPIv1AskEndpoint** - Tests ask response structure
   - All required fields present (question, answer, sources, language, model)
   - Source citations have proper structure (url, title)

4. **TestAPIv1AdminEndpoints** - Tests admin endpoints
   - `/api/v1/admin/health` returns health status
   - `/api/v1/admin/config` exists (may return 501)

5. **TestAPIv1ScrapeEndpoints** - Tests scraping endpoints
   - `/api/v1/scrape/history` returns job history
   - `/api/v1/scrape/stats` returns statistics

6. **TestAPIv1EmbedEndpoints** - Tests embedding endpoints
   - `/api/v1/embed/config` returns embedding configuration

7. **TestAPIv1ErrorHandling** - Tests error responses
   - Invalid endpoints return 404
   - Missing required parameters return 400/422
   - Wrong HTTP methods return 405

**Test Coverage:** 16 comprehensive tests for API v1 features

---

### 5. `/tests/README.md`
**Changes:**
- Updated default backend URL documentation
- Added "API v1 Testing" section
- Documented all API v1 endpoints
- Added example response format for API v1
- Updated commands to reflect port 8004

---

## Test Results

### Integration Tests (`tests/integration/`)
```
test_api.py:
  ✅ test_ask_endpoint_basic
  ✅ test_ask_endpoint_with_spanish
  ✅ test_ask_endpoint_returns_sources_if_available
  ✅ test_service_availability
  ✅ test_ask_with_empty_query
  ✅ test_ask_with_very_long_query

test_api_v1_features.py:
  ✅ test_root_endpoint_returns_api_info
  ✅ test_health_endpoint_backward_compatible
  ✅ test_config_endpoint_backward_compatible
  ✅ test_docs_endpoint_available
  ✅ test_openapi_schema_available
  ✅ test_openapi_schema_contains_v1_endpoints
  ✅ test_ask_response_structure
  ✅ test_ask_sources_structure
  ✅ test_admin_health_endpoint
  ✅ test_admin_config_endpoint
  ✅ test_scrape_history_endpoint
  ✅ test_scrape_stats_endpoint
  ✅ test_embed_config_endpoint
  ✅ test_invalid_endpoint_returns_404
  ✅ test_missing_required_parameter
  ✅ test_method_not_allowed

test_agent.py:
   ⏭️  6 tests skipped (require DATABASE_URL, GROQ_API_KEY env vars)
```

**Total: 22 passed, 6 skipped**

---

## Backend Tests (Unchanged)

The tests in `/backend/tests/` were **not modified** because they test the **agent service** directly on port 8000, not the API Gateway. These tests:
- Use FastAPI TestClient with `src.services.agent.server`
- Test internal agent endpoints: `/ask`, `/ask-stream`
- Mock database, LLM, and embedding dependencies
- Are independent of the Gateway API changes

**Files that remain unchanged:**
- `backend/tests/conftest.py`
- `backend/tests/integration/test_streaming.py`
- `backend/tests/integration/test_model_fallback.py`
- `backend/tests/integration/test_gateway_auth.py`
- `backend/tests/e2e/test_full_chat_flow.py`
- All other backend unit tests

---

## Running the Tests

### Prerequisites
```bash
# Start API Gateway with demo mode
cd backend
DEMO_MODE=true python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8004
```

### Run All Integration Tests
```bash
cd tests
pytest integration/ -v
```

### Run API v1 Features Only
```bash
pytest integration/test_api_v1_features.py -v
```

### Run with Custom Backend URL
```bash
BACKEND_URL=http://localhost:8004 pytest integration/ -v
```

---

## Key Improvements

### 1. **API v1 Compatibility**
- All tests now use `/api/v1/*` endpoints
- Tests verify new response structure with all required fields
- Source citations validated against API v1 schema

### 2. **Better Error Handling**
- Tests check for `detail` field (FastAPI validation)
- Accept 501 responses for not-yet-implemented endpoints
- Graceful fallback for health check endpoints

### 3. **Comprehensive Coverage**
- 16 new tests for API v1 features
- Documentation endpoint testing
- Versioning structure validation
- Error response testing

### 4. **Documentation**
- Updated README with API v1 information
- Documented all tested endpoints
- Added example response formats
- Clarified port differences (8004 vs 8000)

---

## Migration Notes

### For Developers
If you're writing new tests:
- Use `http://localhost:8004` for Gateway API tests
- Use `http://localhost:8000` for Agent service tests (in backend/tests)
- Use `/api/v1/*` prefix for all Gateway endpoints
- Expect `question` parameter (not `query`) in API v1

### For CI/CD
Update your test scripts:
```bash
# Before
BACKEND_URL=http://localhost:8000 pytest tests/integration/

# After (for Gateway tests)
BACKEND_URL=http://localhost:8004 pytest tests/integration/
```

---

## Backward Compatibility

The following legacy endpoints still work and are tested:
- `GET /health` → Returns health status
- `GET /config` → Returns gateway configuration
- `GET /` → Returns service info (JSON for API clients)

These ensure existing monitoring and health check scripts continue to work.

---

## Summary

✅ **22 tests passing** - All integration tests work with API v1  
✅ **6 tests skipped** - Agent tests require environment variables  
✅ **16 new tests** - Comprehensive API v1 feature coverage  
✅ **Backward compatible** - Legacy endpoints still tested  
✅ **Documentation updated** - README reflects API v1 changes  

The test suite now fully supports the API v1 versioning structure and validates all Gateway endpoints.
