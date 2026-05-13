"""Shared pytest configuration and fixtures."""

import os
import sys
from unittest.mock import AsyncMock, MagicMock

import pytest

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
# Pact helpers and other test-only modules live next to this file (``tests/``).
_tests_dir = os.path.dirname(__file__)
if _tests_dir not in sys.path:
    sys.path.append(_tests_dir)

# `EmbeddingClient` and other code paths call `get_config()`, which validates Postgres.
# Unit/integration tests here use mocks and do not need a real database; CI often runs
# without DATABASE_URL/DB_URL set (matches standalone vecinita-scraper Actions).
_db_url = (os.environ.get("DATABASE_URL") or "").strip()
_db_fallback = (os.environ.get("DB_URL") or "").strip()
if not _db_url and not _db_fallback:
    os.environ["DATABASE_URL"] = "postgresql://test:test@127.0.0.1:5432/postgres"


@pytest.fixture
def mock_config():
    """Mock configuration object."""
    config = MagicMock()
    config.environment = "test"
    config.log_level = "DEBUG"
    config.postgres.database_url = "postgresql://postgres:postgres@localhost:5432/vecinita"
    config.api.embedding_upstream_url = "https://test.embedding.api"
    config.api.vecinita_embedding_api_token = "test-token"
    config.crawl.timeout_seconds = 60
    config.chunking.min_size_tokens = 256
    config.chunking.max_size_tokens = 1024
    return config


@pytest.fixture
def mock_db():
    """Mock Postgres database."""
    db = AsyncMock()
    db.create_scraping_job = AsyncMock(return_value="test-job-id")
    db.get_job_status = AsyncMock(return_value={"id": "test-job-id", "status": "pending"})
    db.update_job_status = AsyncMock()
    db.store_crawled_url = AsyncMock(return_value="test-crawled-url-id")
    db.store_extracted_content = AsyncMock(return_value="test-content-id")
    db.store_processed_document = AsyncMock(return_value="test-doc-id")
    db.store_chunks = AsyncMock(return_value=["chunk-1", "chunk-2"])
    db.store_embeddings = AsyncMock()
    return db


@pytest.fixture
def mock_crawl_result():
    """Mock Crawl4AI result."""
    result = MagicMock()
    result.markdown = "# Test Content\nThis is test content."
    result.html = "<h1>Test Content</h1><p>This is test content.</p>"
    result.links = ["https://test.com/page1", "https://test.com/page2"]
    result.media = []
    return result


@pytest.fixture
def sample_scrape_job_request():
    """Sample scrape job request."""
    from vecinita_scraper.core.models import CrawlConfig, ScrapeJobRequest

    return ScrapeJobRequest(
        url="https://example.com",
        user_id="test-user",
        crawl_config=CrawlConfig(max_depth=2),
    )


@pytest.fixture
def sample_chunks():
    """Sample chunks for testing."""
    return [
        {"text": "First chunk text here", "token_count": 50, "semantic_boundary": True},
        {"text": "Second chunk text here", "token_count": 45, "semantic_boundary": False},
        {"text": "Third chunk text here", "token_count": 60, "semantic_boundary": True},
    ]


@pytest.fixture
def sample_embeddings():
    """Sample embeddings."""
    return [
        {
            "chunk_id": "chunk-1",
            "embedding": [0.1] * 384,
            "model_name": "BAAI/bge-small-en-v1.5",
            "dimensions": 384,
        },
        {
            "chunk_id": "chunk-2",
            "embedding": [0.2] * 384,
            "model_name": "BAAI/bge-small-en-v1.5",
            "dimensions": 384,
        },
    ]


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "unit: unit tests")
    config.addinivalue_line("markers", "integration: integration tests")
    config.addinivalue_line(
        "markers",
        "live: tests that hit real APIs (deselect with '-m \"not live\"')",
    )
