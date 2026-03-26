"""
Unit tests for src/gateway/models.py

Tests Pydantic models for request/response validation.
"""

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

pytestmark = pytest.mark.unit


class TestScrapeModels:
    """Test scraping-related models."""

    def test_scrape_request_valid(self):
        """Test valid ScrapeRequest."""
        from src.api.models import LoaderType, ScrapeRequest

        request = ScrapeRequest(
            urls=["https://example.com"],
            force_loader=LoaderType.AUTO,
            stream=False,
        )
        assert request.urls == ["https://example.com"]
        assert request.force_loader == LoaderType.AUTO
        assert request.stream is False

    def test_scrape_request_multiple_urls(self):
        """Test ScrapeRequest with multiple URLs."""
        from src.api.models import ScrapeRequest

        urls = [
            "https://example.com/page1",
            "https://example.com/page2",
            "https://example.com/page3",
        ]
        request = ScrapeRequest(urls=urls)
        assert len(request.urls) == 3
        assert request.urls == urls

    def test_scrape_request_empty_urls_invalid(self):
        """Test that empty URLs list is invalid."""
        from src.api.models import ScrapeRequest

        with pytest.raises(ValidationError):
            ScrapeRequest(urls=[])

    def test_scrape_request_loader_type_enum(self):
        """Test LoaderType enum values."""
        from src.api.models import LoaderType

        assert LoaderType.PLAYWRIGHT.value == "playwright"
        assert LoaderType.RECURSIVE.value == "recursive"
        assert LoaderType.UNSTRUCTURED.value == "unstructured"
        assert LoaderType.AUTO.value == "auto"

    def test_scrape_response(self):
        """Test ScrapeResponse model."""
        from src.api.models import JobStatus, ScrapeResponse

        response = ScrapeResponse(
            job_id="test-job-123",
            status=JobStatus.QUEUED,
            message="Job submitted",
        )
        assert response.job_id == "test-job-123"
        assert response.status == JobStatus.QUEUED
        assert response.message == "Job submitted"

    def test_scrape_job_result(self):
        """Test ScrapeJobResult model."""
        from src.api.models import ScrapeJobResult

        result = ScrapeJobResult(
            total_chunks=50,
            successful_urls=["https://example.com/1", "https://example.com/2"],
            failed_urls=["https://example.com/3"],
            failed_urls_log={"https://example.com/3": "Connection timeout"},
        )
        assert result.total_chunks == 50
        assert len(result.successful_urls) == 2
        assert len(result.failed_urls) == 1

    def test_job_status_enum(self):
        """Test JobStatus enum values."""
        from src.api.models import JobStatus

        assert JobStatus.QUEUED.value == "queued"
        assert JobStatus.RUNNING.value == "running"
        assert JobStatus.COMPLETED.value == "completed"
        assert JobStatus.FAILED.value == "failed"
        assert JobStatus.CANCELLED.value == "cancelled"

    def test_scrape_job_metadata(self):
        """Test ScrapeJobMetadata model."""
        from src.api.models import LoaderType, ScrapeJobMetadata

        metadata = ScrapeJobMetadata(
            job_id="job-123",
            urls=["https://example.com"],
            force_loader=LoaderType.AUTO,
            stream=False,
            created_at=datetime.now(timezone.utc),
        )
        assert metadata.job_id == "job-123"
        assert metadata.created_at is not None
        assert metadata.started_at is None


class TestEmbeddingModels:
    """Test embedding-related models."""

    def test_embed_request(self):
        """Test EmbedRequest model."""
        from src.api.models import EmbedRequest

        request = EmbedRequest(text="Hello world")
        assert request.text == "Hello world"
        assert request.model is None

    def test_embed_request_with_model_override(self):
        """Test EmbedRequest with model override."""
        from src.api.models import EmbedRequest

        request = EmbedRequest(text="Hello world", model="custom-model")
        assert request.model == "custom-model"

    def test_embed_response(self):
        """Test EmbedResponse model."""
        from src.api.models import EmbedResponse

        embedding = [0.1] * 384
        response = EmbedResponse(
            text="Hello world",
            embedding=embedding,
            model="sentence-transformers/all-MiniLM-L6-v2",
            dimension=384,
        )
        assert response.text == "Hello world"
        assert len(response.embedding) == 384
        assert response.dimension == 384

    def test_embed_batch_request(self):
        """Test EmbedBatchRequest model."""
        from src.api.models import EmbedBatchRequest

        texts = ["Hello", "World", "Test"]
        request = EmbedBatchRequest(texts=texts)
        assert len(request.texts) == 3
        assert request.texts == texts

    def test_embed_batch_request_empty_invalid(self):
        """Test that empty texts list is invalid."""
        from src.api.models import EmbedBatchRequest

        with pytest.raises(ValidationError):
            EmbedBatchRequest(texts=[])

    def test_similarity_request(self):
        """Test SimilarityRequest model."""
        from src.api.models import SimilarityRequest

        request = SimilarityRequest(
            text1="Hello world",
            text2="Hello there",
        )
        assert request.text1 == "Hello world"
        assert request.text2 == "Hello there"

    def test_similarity_response(self):
        """Test SimilarityResponse model."""
        from src.api.models import SimilarityResponse

        response = SimilarityResponse(
            text1="Hello",
            text2="Hello",
            similarity=0.99,
            model="test-model",
        )
        assert abs(response.similarity - 0.99) < 0.01
        assert -1 <= response.similarity <= 1

    def test_embedding_config_response(self):
        """Test EmbeddingConfigResponse model."""
        from src.api.models import EmbeddingConfigResponse

        config = EmbeddingConfigResponse(
            model="sentence-transformers/all-MiniLM-L6-v2",
            provider="huggingface",
            dimension=384,
            description="Fast embeddings",
        )
        assert config.model == "sentence-transformers/all-MiniLM-L6-v2"
        assert config.provider == "huggingface"
        assert config.dimension == 384


class TestAskModels:
    """Test Q&A models."""

    def test_ask_request(self):
        """Test AskQuestionRequest model."""
        from src.api.models import AskQuestionRequest

        request = AskQuestionRequest(question="What is housing policy?")
        assert request.question == "What is housing policy?"
        assert request.lang is None
        assert request.provider is None

    def test_ask_request_with_language(self):
        """Test AskQuestionRequest with language specified."""
        from src.api.models import AskQuestionRequest

        request = AskQuestionRequest(
            question="¿Qué es la política de vivienda?",
            lang="es",
        )
        assert request.lang == "es"
        assert request.question == "¿Qué es la política de vivienda?"

    def test_ask_response(self):
        """Test AskQuestionResponse model."""
        from src.api.models import AskQuestionResponse

        response = AskQuestionResponse(
            question="What is housing?",
            answer="Housing is a place where people live.",
            sources=[{"url": "https://example.com", "content": "Sample content", "relevance": 0.9}],
            language="en",
            model="gpt-4",
        )
        assert response.question == "What is housing?"
        assert len(response.sources) == 1
        assert response.language == "en"


class TestAdminModels:
    """Test admin-related models."""

    def test_database_stats(self):
        """Test DatabaseStats model."""
        from src.api.models import DatabaseStats

        stats = DatabaseStats(
            total_chunks=1000,
            unique_sources=50,
            total_embeddings=1000,
            average_chunk_size=512.0,
            db_size_bytes=5000000,
            last_updated=datetime.now(timezone.utc),
        )
        assert stats.total_chunks == 1000
        assert stats.unique_sources == 50
        assert stats.average_chunk_size == 512.0

    def test_document_chunk(self):
        """Test DocumentChunk model."""
        from src.api.models import DocumentChunk

        chunk = DocumentChunk(
            chunk_id="chunk-123",
            source_url="https://example.com",
            content_preview="Sample content preview...",
            embedding_dimension=384,
            created_at=datetime.now(timezone.utc),
        )
        assert chunk.chunk_id == "chunk-123"
        assert chunk.source_url == "https://example.com"
        assert chunk.embedding_dimension == 384

    def test_clean_database_request(self):
        """Test CleanDatabaseRequest model."""
        from src.api.models import CleanDatabaseRequest

        request = CleanDatabaseRequest(confirmation_token="test-token-123")
        assert request.confirmation_token == "test-token-123"

    def test_clean_database_response(self):
        """Test CleanDatabaseResponse model."""
        from src.api.models import CleanDatabaseResponse

        response = CleanDatabaseResponse(
            success=True,
            deleted_chunks=500,
            message="Database cleaned successfully",
        )
        assert response.success is True
        assert response.deleted_chunks == 500


class TestHealthModels:
    """Test health check and config models."""

    def test_health_check(self):
        """Test HealthCheck model."""
        from src.api.models import HealthCheck

        health = HealthCheck(
            status="ok",
            agent_service="ok",
            embedding_service="ok",
            database="ok",
            timestamp=datetime.now(timezone.utc),
        )
        assert health.status == "ok"
        assert health.agent_service == "ok"

    def test_gateway_config(self):
        """Test GatewayConfig model."""
        from src.api.models import GatewayConfig

        config = GatewayConfig(
            agent_url="http://localhost:8000",
            embedding_service_url="http://localhost:8001",
            database_url="postgresql://localhost/test",
            max_urls_per_request=100,
            job_retention_hours=24,
            embedding_model="sentence-transformers/all-MiniLM-L6-v2",
        )
        assert config.agent_url == "http://localhost:8000"
        assert config.embedding_service_url == "http://localhost:8001"
        assert config.max_urls_per_request == 100

    def test_error_response(self):
        """Test ErrorResponse model."""
        from src.api.models import ErrorResponse

        error = ErrorResponse(
            error="Invalid request",
            detail="Missing required field: urls",
            timestamp=datetime.now(timezone.utc),
        )
        assert error.error == "Invalid request"
        assert error.detail == "Missing required field: urls"
