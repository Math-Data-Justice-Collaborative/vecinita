"""
TEST SUITE FOR NEW MODULAR SCRAPER MODULE
==========================================

This directory contains comprehensive tests for the refactored modular scraper
located at src/utils/scraper/

Test Files
==========

1. test_scraper_module.py
   - Core unit tests for all scraper modules
   - Tests for: config, utils, loaders, processors, link_tracker, scraper
   - Configuration loading and management
   - URL utilities and text cleaning
   - Smart loader selection
   - Document processing and chunking
   - Link extraction and tracking
   - Main scraper orchestration

2. test_scraper_cli.py
   - Command-line interface tests
   - Argument parsing and validation
   - Input/output file handling
   - Directory creation
   - Error handling and user interrupts
   - Optional arguments (--links-file, --loader)
   - URL file parsing and filtering

3. test_scraper_advanced.py
   - Edge case handling
   - Integration tests
   - End-to-end pipeline testing
   - File operations
   - Rate limiting verification
   - Error recovery scenarios

Test Markers
============

@pytest.mark.unit
  - Fast, isolated tests with mocked dependencies
  - No external API calls or file system access
  - Safe to run frequently

@pytest.mark.integration
  - Tests that verify component interactions
  - May use temporary files
  - Verify complete pipeline functionality

Running Tests
=============

Run all tests:
  pytest tests/test_scraper*.py -v

Run only unit tests (fast):
  pytest tests/test_scraper*.py -v -m unit

Run only integration tests:
  pytest tests/test_scraper*.py -v -m integration

Run specific test file:
  pytest tests/test_scraper_module.py -v

Run specific test class:
  pytest tests/test_scraper_module.py::TestScraperConfig -v

Run specific test:
  pytest tests/test_scraper_module.py::TestScraperConfig::test_config_initialization -v

Run with coverage:
  pytest tests/test_scraper*.py --cov=src.utils.scraper --cov-report=html

Run tests matching a pattern:
  pytest tests/test_scraper*.py -k "cli" -v

Test Coverage
=============

Current test coverage targets:

✅ src/utils/scraper/config.py
   - Configuration loading from files
   - Recursive site configuration parsing
   - Error handling for missing files
   - Config list parsing with comments

✅ src/utils/scraper/utils.py
   - GitHub URL conversion
   - URL skip pattern matching
   - Playwright requirement detection
   - CSV file detection
   - Crawl config lookup
   - Text cleaning and noise removal
   - File downloading
   - Failed URL logging

✅ src/utils/scraper/loaders.py
   - Smart loader initialization
   - URL skipping logic
   - Forced loader selection
   - CSV file handling
   - Recursive crawling
   - Playwright loading
   - Standard URL loading
   - Error recovery

✅ src/utils/scraper/processors.py
   - Document processing pipeline
   - HTML cleanup with BeautifulSoup
   - Text cleaning integration
   - Document chunking
   - Link extraction
   - Metadata handling
   - File output operations

✅ src/utils/scraper/link_tracker.py
   - Link tracking and deduplication
   - Summary statistics
   - File operations
   - Link organization by source

✅ src/utils/scraper/scraper.py
   - Main orchestrator initialization
   - URL batch processing
   - Statistics tracking
   - Error summary generation
   - Pipeline finalization

✅ src/utils/scraper/main.py
   - CLI argument parsing
   - Input validation
   - Directory creation
   - File parsing
   - Error handling
   - Keyboard interrupt handling

Edge Cases Tested
=================

✓ Empty URL lists
✓ Missing input files
✓ Invalid configuration values
✓ Documents with no metadata
✓ Very large documents
✓ Content with mostly noise
✓ Special characters in URLs
✓ File append operations
✓ Duplicate links
✓ Mixed success/failure scenarios
✓ Keyboard interrupts
✓ Fatal error recovery

Continuous Integration
======================

These tests are designed to run in CI/CD pipelines:
- No hardcoded paths
- No external API dependencies
- Use temporary directories for file operations
- All mocks and fixtures properly scoped
- Exit codes properly handled

Performance Notes
=================

- Unit tests (mark.unit): ~2-5 seconds total
- Integration tests (mark.integration): ~5-10 seconds total
- All tests with coverage reporting: ~10-15 seconds

The tests use mocking extensively to avoid:
- Actual HTTP requests
- File system pollution
- External API dependencies
- Long-running operations

Adding New Tests
================

When adding tests for scraper components:

1. Use appropriate pytest markers (@pytest.mark.unit or @pytest.mark.integration)
2. Create fixtures for common test data
3. Use mocking for external dependencies
4. Test both happy path and error cases
5. Document expected behavior in docstrings
6. Keep tests isolated and independent
7. Use temporary directories for file operations
8. Clean up resources in finally blocks or fixtures

Example test structure:

@pytest.mark.unit
class TestNewFeature:
    \"\"\"Test description.\"\"\"
    
    @pytest.fixture
    def setup(self):
        \"\"\"Set up test fixtures.\"\"\"
        # Create test data
        yield test_data
        # Cleanup
    
    def test_feature_behavior(self, setup):
        \"\"\"Test specific behavior.\"\"\"
        # Arrange
        # Act
        # Assert

Debugging Tests
===============

Run with verbose output:
  pytest tests/test_scraper_module.py -vv

Show print statements:
  pytest tests/test_scraper_module.py -s

Drop into debugger on failure:
  pytest tests/test_scraper_module.py --pdb

Show local variables on failure:
  pytest tests/test_scraper_module.py -l

Stop after first failure:
  pytest tests/test_scraper_module.py -x

Last N test failures:
  pytest tests/test_scraper_module.py --lf

Failed tests only:
  pytest tests/test_scraper_module.py --ff

Troubleshooting
===============

"ModuleNotFoundError: No module named 'src.utils.scraper'"
  → Run from project root directory
  → Ensure __init__.py files exist in all directories
  → Check Python path includes src/

"Permission denied" on temp files
  → Tests use tempfile module (should auto-cleanup)
  → Check no processes have temp files open
  → Try running with elevated privileges

"Timeout" on rate limiting tests
  → Reduce RATE_LIMIT_DELAY value in tests
  → Use faster mocks
  → Check system resources

"""
