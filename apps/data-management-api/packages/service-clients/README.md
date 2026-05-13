# service-clients

Typed async HTTP clients for service-to-service communication in the Vecinita platform.

## Purpose

Instead of each service hand-rolling its own HTTP calls, this package provides:

- `ModelClient` — calls `model-service`
- `EmbeddingClient` — calls `embedding-service`
- `ScraperClient` — calls `scraper-service`

## Usage

Install in any service that needs to call another:

```bash
pip install -e ../../packages/service-clients
```

Example usage:

```python
from service_clients.model_client import ModelClient
from service_clients.embedding_client import EmbeddingClient

model_client = ModelClient(base_url="http://model-service:8002")
embedding_client = EmbeddingClient(base_url="http://embedding-service:8003")

result = await model_client.predict("some text")
embedding = await embedding_client.embed("some text")
```

## Design Rules

- Clients are async (uses `httpx.AsyncClient`)
- Each client is independently instantiable with a configurable `base_url`
- This package **must not** import from any `apps/` service internals
- Only `httpx` and `shared-schemas` are allowed as runtime dependencies
