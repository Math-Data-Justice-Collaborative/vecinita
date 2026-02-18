# Test Organization Guidelines for Vecinita

## Folder Structure

```
vecinita/
├── backend/
│   └── tests/                ← ONLY unit tests here
│       ├── test_*.py         (Fast, isolated, no service dependencies)
│       └── conftest.py       (Backend-only fixtures)
│
├── frontend/
│   └── tests/                ← Frontend unit tests
│       ├── test_*.py
│       └── conftest.py
│
└── tests/                     ← E2E and Integration tests (SEPARATE environment)
    ├── pyproject.toml         (Independent project)
    ├── conftest.py            (Service configuration, fixtures)
    ├── .env.example          (Configuration template)
    ├── test_api_*.py          (Backend API integration tests)
    ├── test_e2e_*.py          (Frontend E2E tests with Playwright)
    ├── test_ui_*.py           (UI component tests)
    └── utils.py               (Shared test utilities)
```

## Test Classification

### Unit Tests → backend/tests/
- ✅ Fast (< 1 second)
- ✅ No external services
- ✅ All dependencies mocked
- ✅ Can run independently of other services
- ✅ Examples:
  - `test_supabase_embeddings.py`
  - `test_static_response_tool.py`
  - `test_db_search_tool.py`

### Integration Tests → tests/ (root)
- ✅ Requires running backend service
- ✅ Tests API endpoints
- ✅ Tests data flow through agent
- ✅ Tests database connections
- ✅ Examples:
  - `test_api_*.py` - Backend API integration
  - `test_agent_*.py` - Agent with real services
  - Tests marked with `@pytest.mark.integration`

### E2E Tests → tests/ (root)
- ✅ Requires both backend AND frontend running
- ✅ Tests user workflows using Playwright
- ✅ Tests frontend UI interactions
- ✅ Tests backend-frontend communication
- ✅ Examples:
  - `test_e2e_*.py` - User workflows
  - Tests marked with `@pytest.mark.e2e`

## Migration Path for Integration Tests

Some tests currently in `backend/tests/` are marked as `@pytest.mark.integration`:
- `test_agent_langgraph.py` - MOVE to `tests/`
- `test_scraper_advanced.py` - CONSIDER MOVING or mark unit/integration clearly
- `test_scraper_module.py` - CONSIDER MOVING or mark unit/integration clearly

### How to Migrate

1. **Review the test**: Check if it requires running services
   ```bash
   grep -A 5 "@pytest.mark.integration" backend/tests/test_agent_langgraph.py
   ```

2. **Copy to root tests**:
   ```bash
   cp backend/tests/test_agent_langgraph.py tests/test_agent_integration.py
   ```

3. **Update imports** in the test file:
   - If importing from `src.agent.*`, add backend path setup to conftest.py
   - Prefer using HTTP client over direct imports
   - Use fixtures from root conftest.py: `backend_url`, `api_timeout`

4. **Remove from backend/tests** only after confirming it works in root:
   ```bash
   rm backend/tests/test_agent_langgraph.py
   ```

5. **Test both locations**:
   ```bash
   # Backend unit tests
   cd backend && uv run pytest tests/ -m "not integration"
   
   # Root integration tests  
   cd tests && uv run pytest -m integration
   ```

## Running Tests by Category

### Only Unit Tests (Backend)
```bash
cd backend
uv run pytest tests/ -m "not integration"
# Or skip integration marker
uv run pytest tests/ -k "not _integration"
```

### Only Integration Tests
```bash
cd tests
uv run pytest -m integration
```

### Only E2E Tests
```bash
cd tests
uv run pytest -m e2e
```

### ALL Tests
```bash
# Start services in separate terminals
cd backend && uv run uvicorn src.agent.main:app --reload
cd frontend && npm run dev

# Run all tests
cd tests && uv run pytest
```

## Why Separate Folders?

1. **CI/CD Efficiency**: Unit tests run fast without starting services
2. **Isolation**: Integration tests don't pollute backend with service dependencies
3. **Clear Intent**: Test location indicates what it tests
4. **Dependency Management**: Root tests has minimal backend dependencies
5. **Team Clarity**: 
   - Backend team: Focus on fast unit tests
   - QA team: Focus on E2E tests
   - Integration team: Focus on API contracts

## Environment Variables by Folder

### backend/tests/
- None required for unit tests
- All external services mocked

### tests/ (Integration & E2E)
```bash
BACKEND_URL=http://localhost:8000
FRONTEND_URL=http://localhost:5173
SKIP_E2E=false
PLAYWRIGHT_HEADLESS=true
```

## Checklist for Test Organization

- [ ] Backend unit tests have no `@pytest.mark.integration`
- [ ] Backend unit tests don't make HTTP calls
- [ ] Root tests folder has independent pyproject.toml
- [ ] Root tests use fixtures: `backend_url`, `frontend_url`
- [ ] Integration tests use APIClient from utils.py
- [ ] E2E tests use Playwright instead of direct imports
- [ ] All tests have appropriate markers: `@pytest.mark.integration`, `@pytest.mark.e2e`
- [ ] CI/CD skips integration tests when services unavailable
- [ ] README explains how to run each category

## Example: Moving test_agent_langgraph.py

**Before** (in backend/tests):
```python
# backend/tests/test_agent_langgraph.py
from src.agent.main import app  # Direct import from backend
...
```

**After** (in root/tests):
```python
# tests/test_agent_integration.py
# Instead of direct import, use APIClient
from utils import APIClient

@pytest.mark.integration
def test_agent(api_client):
    response = api_client.ask("What is Vecinita?")
    assert response.status_code == 200
```

This way, tests are truly independent and don't need backend code in their environment.
