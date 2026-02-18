"""
Embedding Service Package

Lightweight FastAPI service for text embeddings using sentence-transformers.
Runs as a separate Render free-tier service (512MB limit).

Endpoints:
  - GET /health - Health check
  - POST /embed - Single text embedding
  - POST /embed-batch - Batch text embeddings
  - POST /similarity - Find similar texts
  - GET / - Service info

Example usage:
  from src.services.embedding.client import create_embedding_client
  
  client = create_embedding_client("http://localhost:8001")
  embedding = client.embed_query("hello world")
  print(embedding)  # [0.123, -0.456, ..., 384-dim vector]
"""

__version__ = "0.1.0"
__author__ = "Vecinita Team"
__all__ = ["main", "client"]
