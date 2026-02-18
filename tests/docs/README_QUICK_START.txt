╔═══════════════════════════════════════════════════════════════════════════════╗
║                  VECINITA E2E/INTEGRATION TESTS - QUICK START                 ║
╚═══════════════════════════════════════════════════════════════════════════════╝

INDEPENDENT TEST ENVIRONMENT
════════════════════════════════════════════════════════════════════════════════

This folder (/tests) is a SEPARATE PROJECT from the backend.

✓ Has its own pyproject.toml
✓ Has its own dependencies
✓ Has its own pytest configuration
✓ Does NOT import backend code directly
✓ Tests via HTTP API calls instead


SETUP (5 MINUTES)
════════════════════════════════════════════════════════════════════════════════

1. Install dependencies:
   cd tests
   uv sync

2. Create environment file:
   cp .env.example .env
   # Edit .env if backend/frontend are on different URLs

3. Start services (in separate terminals):
   
   Terminal 1 - Backend:
   cd backend
   uv run uvicorn src.agent.main:app --reload
   
   Terminal 2 - Frontend (if doing E2E):
   cd frontend
   npm install
   npm run dev
   
   Terminal 3 - Tests:
   cd tests
   uv run pytest


RUNNING TESTS
════════════════════════════════════════════════════════════════════════════════

Run ALL tests (requires backend + frontend):
   uv run pytest -v

Run INTEGRATION tests only (requires backend):
   uv run pytest -v -m integration

Run E2E tests only (requires backend + frontend):
   uv run pytest -v -m e2e

Run API tests only (requires backend):
   uv run pytest -v -m api

Run SPECIFIC test file:
   uv run pytest test_api_integration.py -v

Run with HEADLESS BROWSER (see what Playwright does):
   PLAYWRIGHT_HEADLESS=false uv run pytest -v -m e2e

Skip E2E tests (faster):
   SKIP_E2E=true uv run pytest -v


TEST MARKERS
════════════════════════════════════════════════════════════════════════════════

@pytest.mark.integration    Tests requiring running backend service
@pytest.mark.e2e            Tests requiring Playwright + services
@pytest.mark.api            API endpoint tests
@pytest.mark.backend_required   Tests requiring backend
@pytest.mark.frontend_required  Tests requiring frontend
@pytest.mark.requires_services  Tests requiring both services


TROUBLESHOOTING
════════════════════════════════════════════════════════════════════════════════

Q: "connection refused"
A: Is backend running on http://localhost:8000?
   Check: curl http://localhost:8000/docs

Q: "playwright not found"
A: Install: uv run playwright install

Q: "socket timeout"
A: Increase timeout in .env: API_TIMEOUT=30

Q: "tests hang"
A: Backend might be slow. Try skipping E2E: SKIP_E2E=true


FILE STRUCTURE
════════════════════════════════════════════════════════════════════════════════

tests/
├── pyproject.toml          ← Independent project config
├── conftest.py             ← Pytest config + fixtures
├── .env.example            ← Configuration template
├── .env                    ← Your local config (git ignored)
├── utils.py                ← Shared test utilities
├── test_api_integration.py ← API integration tests
├── test_e2e_sources.py     ← E2E source tests
├── test_agent_integration.py ← Agent integration tests
└── .gitignore


KEY CONCEPTS
════════════════════════════════════════════════════════════════════════════════

✓ Integration Tests: Test backend API with real services running
  - Response time: 1-5 seconds
  - Requires: Backend service only
  - Use: APIClient from utils.py

✓ E2E Tests: Test user workflows with Playwright browser
  - Response time: 5-30 seconds
  - Requires: Backend + Frontend services
  - Use: Playwright from conftest fixtures

✓ Unit Tests: In backend/tests/ (FAST, < 1 second each)
  - Response time: < 1 second
  - Requires: None (all mocked)
  - Run: cd backend && pytest tests/


ENVIRONMENT VARIABLES
════════════════════════════════════════════════════════════════════════════════

BACKEND_URL         Backend service URL (default: http://localhost:8000)
FRONTEND_URL        Frontend service URL (default: http://localhost:5173)
SKIP_E2E           Skip E2E tests (true/false)
SKIP_INTEGRATION   Skip integration tests (true/false)
PLAYWRIGHT_HEADLESS Run browser headless (true/false, default: true)
API_TIMEOUT        API request timeout in seconds (default: 10)
E2E_TIMEOUT        E2E test timeout in seconds (default: 30)


MORE INFO
════════════════════════════════════════════════════════════════════════════════

See README.md for detailed documentation
See ../TEST_ORGANIZATION.md for test organization guidelines
See ../backend/tests/ for unit tests (fast, no services)

