# Backend Tests Documentation

This folder contains detailed documentation about the backend test suite.

## 📚 Contents

- **[INDEX.md](INDEX.md)** - Test documentation index
- **[README_SCRAPER_TESTS.md](README_SCRAPER_TESTS.md)** - Scraper test details
- **[SCRAPER_TESTS_SUMMARY.md](SCRAPER_TESTS_SUMMARY.md)** - Scraper test summary
- **[TEST_SCRAPER_MODULE.md](TEST_SCRAPER_MODULE.md)** - Scraper module tests guide

## 🚀 Helper Scripts

- **[run_tests.bat](run_tests.bat)** - Windows test runner script
- **[run_tests.sh](run_tests.sh)** - Unix/Linux test runner script

> **Note**: These scripts are legacy helpers. The recommended way to run tests is:
> ```bash
> cd backend && uv run pytest
> ```

## 📖 Main Guides

For the main test documentation, see:
- **[../README.md](../README.md)** - Comprehensive backend tests guide
- **[../CLEANUP_REPORT.md](../CLEANUP_REPORT.md)** - Integration test identification

Recent coverage additions:
- `backend/tests/test_embedding_service_client.py` (embedding service token headers)
- `backend/tests/test_api/test_gateway_router_scrape.py` (`/api/v1/scrape/reindex` endpoint)
- `backend/tests/integration/test_modal_reindex_trigger.py` (gateway → Modal reindex integration)
- `backend/tests/e2e/test_reindex_flow.py` (end-to-end trigger behavior)

## 🔗 Related Documentation

- [Backend Contributing Guide](../../CONTRIBUTING.md)
- [Root Tests README](../../../tests/README.md) - Cross-service E2E tests
- [Documentation Index](../../../docs/INDEX.md)
