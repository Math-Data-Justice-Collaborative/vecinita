# Vecinita Test Suite

Comprehensive testing suite for the Vecinita RAG Q&A system using pytest and Playwright.

## Overview

This test suite covers:
- **Unit tests** for all utility modules and the FastAPI application
- **Integration tests** for database and API interactions
- **UI tests** using Playwright for end-to-end testing

## Gateway API v1 Integration Matrix

Gateway contract coverage is tracked in:

- `tests/integration/MATRIX_GATEWAY_V1.md` (endpoint matrix)
- `tests/integration/MATRIX_INTEGRATION_POINTS.md` (integration point mapping)

Matrix contract enforcement:

```bash
uv run pytest tests/integration/test_gateway_v1_matrix_coverage.py -q
```

This check fails if any Gateway API v1 endpoint exists in router source but is missing from the matrix file.

## Test Structure

```
tests/
├── __init__.py
├── conftest.py              # Shared fixtures and configuration
├── test_main.py             # FastAPI application tests
├── test_faq_loader.py       # FAQ loading tests
├── test_load_faq.py         # Alternative FAQ loader tests
├── test_scraper_to_text.py  # Web scraper tests
├── test_supabase_db_test.py # Database connection tests
├── test_vector_loader.py    # Vector database loader tests
└── test_ui.py               # UI tests with Playwright
```

## Installation

### Install Test Dependencies

```bash
# Install pytest and required plugins
pip install pytest pytest-asyncio

# For async tests and UI testing
pip install playwright

# Install Playwright browsers (required for UI tests)
playwright install
```

Or using UV:

```bash
uv pip install pytest pytest-asyncio playwright
uv run playwright install
```

## Running Tests

### Run All Tests

```bash
pytest
```

### Run Specific Test Categories

```bash
# Unit tests only (fast)
pytest -m unit

# Integration tests
pytest -m integration

# UI tests (requires server running)
pytest -m ui

# Database tests
pytest -m db

# API tests
pytest -m api
```

### Run Specific Test Files

```bash
# Test main.py
pytest tests/test_main.py

# Test FAQ loader
pytest tests/test_faq_loader.py

# Test scraper
pytest tests/test_scraper_to_text.py

# Test vector loader
pytest tests/test_vector_loader.py
```

### Run Tests with Verbose Output

```bash
pytest -v
```

### Run Tests with Coverage

```bash
pytest --cov=. --cov-report=html
```

## UI Tests with Playwright

### Prerequisites

1. **Install Playwright browsers:**
   ```bash
   playwright install
   ```

2. **Start the development server:**
   ```bash
   uv run uvicorn main:app --host localhost --port 8000
   ```

3. **Run UI tests:**
   ```bash
   # The UI tests are skipped by default
   # To run them, remove the @pytest.mark.skip decorators or use:
   pytest tests/test_ui.py --run-skipped -m ui -v
   ```

### UI Test Coverage

- Page load and initialization
- Input element validation
- Submit button functionality
- Spanish language question handling
- API endpoint integration
- Response display
- Responsive design (mobile/desktop)
- Performance metrics
- Error handling
- Console error detection

## Test Configuration

### pytest.ini

Configuration file for pytest with:
- Test discovery patterns
- Test markers for categorization
- Logging configuration
- Output formatting

### conftest.py

Shared pytest fixtures:
- `env_vars` - Environment variables
- `mock_supabase_client` - Mocked Supabase client
- `mock_embedding_model` - Mocked embedding model
- `mock_llm` - Mocked language model
- `fastapi_client` - FastAPI test client
- `temp_file` - Temporary file for testing
- `sample_documents` - Sample document data
- `sample_chunks` - Sample document chunks

## Test Markers

Tests are organized with markers for easy filtering:

- `@pytest.mark.unit` - Unit tests (no external dependencies)
- `@pytest.mark.integration` - Integration tests (may require services)
- `@pytest.mark.ui` - UI tests using Playwright
- `@pytest.mark.db` - Database-related tests
- `@pytest.mark.api` - API endpoint tests
- `@pytest.mark.slow` - Long-running tests

## Mocking Strategy

The test suite uses mocking extensively to:
- Avoid external dependencies during testing
- Isolate units of code for testing
- Control test data and responses
- Speed up test execution

Key mocked components:
- Supabase client and database operations
- Embedding models (HuggingFace, OpenAI)
- Language models (ChatGroq, ChatOpenAI)
- File I/O operations
- HTTP requests

## Environment Variables for Testing

Tests use a `.env` file for configuration. Create a `.env.test` file or set environment variables:

```
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-api-key
GROQ_API_KEY=your-groq-key
DATABASE_URL=postgresql://user:password@localhost/db
```

## Continuous Integration

These tests are designed to run in CI/CD pipelines:

```bash
# Run with minimal output for CI
pytest --tb=short -q

# Generate coverage report
pytest --cov=. --cov-report=xml

# Run specific tests matching pattern
pytest -k "test_ask" -v
```

## Troubleshooting

### Playwright Tests Not Running

1. Ensure browsers are installed:
   ```bash
   playwright install
   ```

2. Ensure the server is running:
   ```bash
   uv run uvicorn main:app --host localhost --port 8000
   ```

3. Remove `@pytest.mark.skip` decorators from UI tests

### Import Errors

1. Ensure you're in the correct directory:
   ```bash
   cd /path/to/vecinita
   ```

2. Ensure dependencies are installed:
   ```bash
   pip install -e .
   ```

### Mocking Issues

If mocks aren't working correctly:
1. Check the import path matches the patch path
2. Ensure patch is applied before the code under test runs
3. Verify mock return values are set correctly

## Writing New Tests

### Test File Template

```python
import pytest
from unittest.mock import patch, MagicMock

@pytest.mark.unit
class TestMyFeature:
    """Test my feature."""
    
    def test_something(self, fastapi_client, mock_supabase_client):
        """Test description."""
        # Arrange
        expected = "result"
        
        # Act
        result = my_function()
        
        # Assert
        assert result == expected
```

### Using Fixtures

```python
def test_with_fixtures(
    fastapi_client,
    mock_supabase_client,
    mock_embedding_model,
    sample_documents
):
    """Test using built-in fixtures."""
    # Use fixtures...
    pass
```

## Best Practices

1. **Name tests descriptively**: `test_ask_english_question` is better than `test_ask`
2. **Use arrange-act-assert pattern**: Setup, execute, verify
3. **Keep tests isolated**: No dependencies between tests
4. **Mock external services**: Don't make real API calls
5. **Test edge cases**: Empty inputs, errors, timeouts
6. **Document complex setups**: Add comments explaining mocks

## Performance

- Unit tests run in < 1 second
- Integration tests run in < 5 seconds
- UI tests run in < 10 seconds per test (requires running server)

Run only unit tests for fast feedback during development:

```bash
pytest -m unit
```

## Contributing

When adding new features:
1. Write tests first (TDD approach)
2. Ensure all existing tests pass
3. Add tests for edge cases and error conditions
4. Update this README if adding new test categories
5. Maintain > 80% code coverage

## Coverage Goals

- Core functionality: 90%+
- Utilities: 85%+
- Integration points: 80%+
- Overall target: 85%

Check coverage:

```bash
pytest --cov=. --cov-report=term-missing
```

## Resources

- [pytest documentation](https://docs.pytest.org/)
- [Playwright Python docs](https://playwright.dev/python/)
- [unittest.mock documentation](https://docs.python.org/3/library/unittest.mock.html)
- [FastAPI testing](https://fastapi.tiangolo.com/advanced/testing-dependencies/)
