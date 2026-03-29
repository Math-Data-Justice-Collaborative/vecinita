"""ASGI entrypoint for local embedding service in microservices compose runs.

This wrapper initializes the embedding model once and exposes the service app
used by local contract/integration environments.
"""

from fastembed import TextEmbedding

from vecinita.api import create_app
from vecinita.constants import DEFAULT_MODEL, MODEL_DIR
from vecinita.service import EmbeddingService


_embedding = TextEmbedding(model_name=DEFAULT_MODEL, cache_dir=MODEL_DIR)
# Warm model so first request latency is stable in local integration runs.
list(_embedding.embed(["warmup"]))

app = create_app(EmbeddingService(_embedding, default_model=DEFAULT_MODEL))
