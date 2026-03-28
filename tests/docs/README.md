# E2E and Integration Tests

This folder contains end-to-end and integration tests for Vecinita. These tests run **independently** as a separate environment and test the interaction between backend and frontend services.

## Architecture

```
/tests/                    ← Independent test environment
├── pyproject.toml         (Separate project configuration)
├── conftest.py            (Pytest configuration, fixtures, environment setup)
├── test_e2e_sources.py    (E2E tests using Playwright)
├── test_api_*.py          (Integration tests - backend API)
├── test_ui_*.py           (Frontend UI tests - Playwright)
└── .env.example           (Configuration template)

/backend/tests/            ← Backend unit tests ONLY
├── test_*.py              (Fast, isolated unit tests)
└── conftest.py            (Backend-specific fixtures)

/frontend/tests/           ← Frontend unit tests (if present)
```

## Test Types

### Unit Tests (Backend)
- **Location**: `backend/tests/`
- **Speed**: Fast (< 1 second each)
- **Dependencies**: None (all mocked)
- **Run with**: `cd backend && pytest tests/ -m "not integration"`

### Integration Tests (API)
- **Location**: `tests/test_api_*.py`
- **Marker**: `@pytest.mark.integration`
- **Speed**: Medium (1-5 seconds each)
- **Requirements**: Running backend service
- **Tests**: Backend endpoints, data flow, agent logic

### E2E Tests (Frontend + Backend)
- **Location**: `tests/test_e2e_*.py`
- **Marker**: `@pytest.mark.e2e`
- **Speed**: Slow (5-30 seconds each)
- **Requirements**: Running backend AND frontend services
- **Tests**: User workflows, UI interactions, full system

## Setup

### 1. Install Test Dependencies

This folder is a separate project with its own dependencies:

```bash
cd tests
uv sync          # Install from pyproject.toml
# OR
pip install -e .
```

### 2. Configure Environment

```bash
cd tests
cp .env.example .env
# Edit .env with your service URLs
```

### 3. Start Services (in separate terminals)

```bash
# Terminal 1: Backend service
cd backend
uv run uvicorn src.agent.main:app --reload

# Terminal 2: Frontend service (Vite dev server)
cd frontend
npm install
npm run dev

# Terminal 3: Run tests
cd tests
uv run pytest
```

## Running Tests

### Run all tests (requires both services)
```bash
uv run pytest -v
```

### Run only API tests (requires backend)
```bash
uv run pytest -v -m api
```

### Run only E2E tests (requires backend + frontend)
```bash
uv run pytest -v -m e2e
```

### Run only integration tests
```bash
uv run pytest -v -m integration
```

### Skip E2E tests (faster)
```bash
SKIP_E2E=true uv run pytest -v
```

### Run with Playwright browser visible
```bash
PLAYWRIGHT_HEADLESS=false uv run pytest -v -m e2e
```

### Run single test file
```bash
uv run pytest test_e2e_sources.py -v
```

### Run with coverage
```bash
uv run pytest --cov=. --cov-report=html
```

## Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `BACKEND_URL` | `http://localhost:8000` | Backend API URL |
| `FRONTEND_URL` | `http://localhost:5173` | Frontend dev server URL |
| `SKIP_E2E` | `false` | Skip E2E tests |
| `SKIP_INTEGRATION` | `false` | Skip integration tests |
| `PLAYWRIGHT_HEADLESS` | `true` | Run Playwright headless |
| `API_TIMEOUT` | `10` | API call timeout (seconds) |
| `E2E_TIMEOUT` | `30` | E2E test timeout (seconds) |

## Test Structure

### Integration Test Example
```python
@pytest.mark.integration
@pytest.mark.backend_required
class TestAskEndpoint:
    """Integration tests for /ask endpoint."""
    
    def test_ask_returns_answer(self, backend_url):
        """Test that /ask endpoint returns an answer."""
        response = requests.get(
            f"{backend_url}/ask",
            params={"query": "What is Vecinita?"}
        )
        assert response.status_code == 200
        assert "answer" in response.json()
```

### E2E Test Example
```python
@pytest.mark.e2e
@pytest.mark.requires_services
class TestUserWorkflow:
    """E2E tests using Playwright for user workflows."""
    
    @pytest.mark.asyncio
    async def test_ask_question_workflow(self, frontend_url):
        """Test complete user workflow of asking a question."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            await page.goto(frontend_url)
            # ... test interactions ...
            await browser.close()
```

## CI/CD Usage

### In GitHub Actions

```yaml
- name: Run E2E Tests
  env:
    BACKEND_URL: ${{ secrets.BACKEND_URL }}
    FRONTEND_URL: ${{ secrets.FRONTEND_URL }}
    SKIP_E2E: false
  run: |
    cd tests
    uv sync
    uv run pytest -v --cov
```

### Skip tests when services unavailable

```bash
# Tests auto-skip if services aren't reachable
uv run pytest  # E2E tests skip if services down
```

## Troubleshooting

### Tests fail with "connection refused"
- Ensure backend is running: `http://localhost:8000`
- Ensure frontend is running: `http://localhost:5173`
- Check `BACKEND_URL` and `FRONTEND_URL` in `.env`

### Playwright tests fail
```bash
# Install Playwright browsers
uv run playwright install

# Or run with system Playwright
export PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1
```

### Tests timeout
- Increase `API_TIMEOUT` or `E2E_TIMEOUT` in `.env`
- Check service performance: `curl -v http://localhost:8000/health`

## Best Practices

1. **Use fixtures for service URLs**: `backend_url`, `frontend_url` provided by conftest.py
2. **Mark tests appropriately**: `@pytest.mark.e2e`, `@pytest.mark.integration`
3. **Don't depend on backend code**: Import from frontend only
4. **Use timeouts**: All API calls should have timeouts
5. **Clean up resources**: Close browsers, connections properly
6. **Make tests independent**: Each test should work in isolation

## Development Workflow

```bash
# 1. Make changes to backend or frontend
# 2. Start services in separate terminals
# 3. Run tests to verify
cd tests
uv run pytest -v tests/test_e2e_*.py

# 4. Debug with headless=false
PLAYWRIGHT_HEADLESS=false uv run pytest test_e2e_*.py -s

# 5. Commit changes with passing tests
```

## Integration with Backend/Frontend

- **Backend changes**: Run backend unit tests first, then E2E
- **Frontend changes**: Run frontend unit tests first, then E2E
- **API contract changes**: Update both test and backend
- **UI changes**: Update Playwright selectors in E2E tests

