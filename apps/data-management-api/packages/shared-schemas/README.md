# shared-schemas

Shared Pydantic schemas, API request/response types, and data contracts used across all Vecinita services.

## Purpose

This package is the **single source of truth** for:

- API request and response models
- Shared data structures (e.g., scraped records, predictions, embeddings)
- Event schemas for async workflows

## Usage

Install in any service:

```bash
pip install -e ../../packages/shared-schemas
```

Import in your code:

```python
from shared_schemas.model import PredictRequest, PredictResponse
from shared_schemas.embedding import EmbedRequest, EmbedResponse
from shared_schemas.scraper import ScrapeRequest, ScrapeResult
```

## Design Rules

- This package **must not** import from any `apps/` service
- Only `pydantic` is allowed as a runtime dependency
- Keep schemas small and focused — avoid business logic here
