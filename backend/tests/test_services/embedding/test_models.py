import pytest
from pydantic import ValidationError

from src.services.embedding.models import (
    BatchEmbeddingResult,
    Dimensionality,
    EmbeddingModel,
    EmbeddingResult,
    EmbeddingServiceConfig,
    SimilarityScore,
)


def test_embedding_model_defaults():
    model = EmbeddingModel(name="bge-small", provider="fastembed", dimension=384)

    assert model.description == ""
    assert model.active is True


def test_embedding_service_config_defaults():
    config = EmbeddingServiceConfig(model_name="sentence-transformers/all-MiniLM-L6-v2")

    assert config.provider == "huggingface"
    assert config.dimension == 384
    assert config.batch_size == 32
    assert config.cache_embeddings is True


def test_embedding_result_and_batch_result_round_trip():
    item = EmbeddingResult(
        text="hello",
        embedding=[0.1, 0.2],
        model="mini",
        dimension=2,
        processing_time_ms=12.5,
    )
    batch = BatchEmbeddingResult(
        embeddings=[item],
        model="mini",
        dimension=2,
        batch_size=1,
        total_processing_time_ms=14.0,
    )

    assert batch.embeddings[0].text == "hello"
    assert batch.total_processing_time_ms == 14.0


def test_similarity_score_validates_range():
    score = SimilarityScore(text1="a", text2="b", similarity=0.5, model="mini")
    assert score.similarity == 0.5

    with pytest.raises(ValidationError):
        SimilarityScore(text1="a", text2="b", similarity=1.5, model="mini")


def test_dimensionality_fields():
    dimensionality = Dimensionality(model="mini", dimension=384, provider="fastembed")

    assert dimensionality.model == "mini"
    assert dimensionality.dimension == 384
    assert dimensionality.provider == "fastembed"
