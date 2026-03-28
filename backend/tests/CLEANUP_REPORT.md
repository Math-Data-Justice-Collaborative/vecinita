# Backend Tests Cleanup Report

**Date**: February 7, 2026  
**Reviewer**: GitHub Copilot  
**Goal**: Identify integration/E2E tests and clean up backend/tests directory

## 🔍 Integration/E2E Tests Found

The following tests in `backend/tests/` have integration or E2E characteristics and **should remain in backend/tests/** for backend-specific integration testing:

### 1. **test_agent_langgraph.py** (133 lines)
- **Type**: Integration test
- **Status**: ✅ Already properly marked
- **Markers**: `pytestmark = pytest.mark.skipif(...)`
- **Requirements**: 
  - SUPABASE_URL, SUPABASE_KEY, GROQ_API_KEY environment variables
  - Active Supabase database with RPC functions
  - Network connectivity
- **Reason**: This tests the FastAPI app with LangGraph agent using TestClient
- **Keep in**: `backend/tests/` (backend-specific integration)

### 2. **test_scraper_advanced.py** - TestScraperPipelineEnd2End class (line 165+)
- **Type**: Integration test class
- **Marker**: `@pytest.mark.integration`
- **Tests**: Complete scraping pipeline with mocked loaders
- **Reason**: Tests scraper module end-to-end behavior
- **Keep in**: `backend/tests/` (backend unit/integration mix)

### 3. **test_scraper_module.py** - Integration tests (line 465+)
- **Type**: Integration tests
- **Marker**: `@pytest.mark.integration`
- **Tests**: Scraper module component integration
- **Reason**: Tests scraper components working together
- **Keep in**: `backend/tests/` (backend unit/integration mix)

### 4. **test_supabase_embeddings.py** - TestIntegration class (line 193+)
- **Type**: Integration test class (currently skipped)
- **Marker**: `@pytest.mark.skipif(True, ...)`
- **Requirements**: Deployed Supabase edge function
- **Status**: Manual test only (skipif=True)
- **Keep in**: `backend/tests/` (backend-specific integration)

## ✅ Recommendation

**All integration/E2E tests should STAY in backend/tests/** because:

1. They test backend-specific functionality (agent, scraper, embeddings)
2. They use backend imports and backend-specific tools
3. They are properly marked with `@pytest.mark.integration` or `skipif`
4. Separation between unit and integration is achieved via pytest markers

The `/tests` folder in the repository root is for **cross-service E2E tests** that test backend ↔ frontend interactions.

## 📊 Test Organization Strategy

```
vecinita/
├── backend/tests/          ← Backend unit + integration tests
│   ├── test_*.py          # Unit tests (no markers)
│   └── test_*.py          # Integration tests (@pytest.mark.integration)
│
└── tests/                  ← Cross-service E2E tests
    ├── integration/       # Backend API integration (HTTP client)
    └── e2e/              # Full stack E2E (Playwright)
```

### Run Strategies

```bash
# Backend unit tests only
cd backend && uv run pytest -m "not integration"

# Backend integration tests only
cd backend && uv run pytest -m integration

# All backend tests
cd backend && uv run pytest

# Cross-service E2E tests
cd tests && uv run pytest -v
```

## 🧹 Backend Tests Cleanup Tasks

### Files to Organize

#### Documentation Files
- ✅ `INDEX.md` (7KB) - Keep, but move to docs/
- ✅ `README.md` (7KB) - Keep as main tests README
- ⚠️ `README_SCRAPER_TESTS.md` (9KB) - Move to docs/
- ⚠️ `SCRAPER_TESTS_SUMMARY.md` (7KB) - Move to docs/
- ⚠️ `TEST_SCRAPER_MODULE.md` (6KB) - Move to docs/

#### Temporary/Log Files
- ❌ `pytest.log` (110KB) - Delete and add to .gitignore
- ❌ `__pycache__/` - Already in .gitignore

#### Script Files
- ⚠️ `run_tests.bat` (2.7KB) - Move to docs/ or delete (redundant with `uv run pytest`)
- ⚠️ `run_tests.sh` (3KB) - Move to docs/ or delete (redundant with `uv run pytest`)

### Proposed Structure

```
backend/tests/
├── README.md                          ← Main tests documentation
├── conftest.py                        ← Pytest configuration
├── docs/                              ← NEW: Test documentation folder
│   ├── INDEX.md
│   ├── README_SCRAPER_TESTS.md
│   ├── SCRAPER_TESTS_SUMMARY.md
│   ├── TEST_SCRAPER_MODULE.md
│   ├── run_tests.bat
│   └── run_tests.sh
├── test_agent_langgraph.py           ← Integration test (marked)
├── test_clarify_question_tool.py     ← Unit test
├── test_db_search_tool.py            ← Unit test (mocked)
├── test_faq.py                       ← Unit test
├── test_html_cleaner.py              ← Unit test
├── test_scraper_advanced.py          ← Mixed (has @pytest.mark.integration)
├── test_scraper_cli.py               ← Unit test
├── test_scraper_enhancements.py      ← Unit test
├── test_scraper_module.py            ← Mixed (has @pytest.mark.integration)
├── test_scraper_upload_chunks.py     ← Unit test
├── test_static_response_tool.py      ← Unit test
├── test_supabase_embeddings.py       ← Unit + Integration (marked)
└── test_web_search_tool.py           ← Unit test (mocked)
```

## 📝 .gitignore Updates

Add to `backend/.gitignore`:
```
# Test artifacts
tests/pytest.log
tests/__pycache__/
*.pytest_cache/
.coverage
htmlcov/
```

## ✅ Action Items

1. ✅ Create `backend/tests/docs/` directory
2. ✅ Move documentation files to `backend/tests/docs/`
3. ✅ Delete `pytest.log`
4. ✅ Update `backend/.gitignore` to ignore test artifacts
5. ✅ Update `backend/tests/README.md` to reflect new structure
6. ✅ Keep all test files in `backend/tests/` (no moves needed)

---

**Status**: Ready for cleanup
