# Embedding Endpoints Implementation Guide

## Overview

The embedding router (`backend/src/api/router_embed.py`) provides 5 fully-implemented endpoints for text embedding generation, batch processing, and similarity computation. All endpoints proxy requests to the dedicated embedding microservice running on port 8001.

## Architecture

**API Gateway (port 8002)** → **Embedding Service (port 8001)**

The API gateway acts as a proxy, providing:
- Request validation via Pydantic models
- Error handling and service availability checks
- Consistent response formatting
- Optional authentication/rate limiting (via middleware)

The embedding service:
- Runs sentence-transformers models locally
- Provides fast, efficient embedding generation
- Supports model switching and configuration

## Endpoints

### 1. Generate Single Embedding
**POST `/api/embed/`**

Generate embedding vector for a single text string.

**Request Body:**
```json
{
  "text": "The quick brown fox jumps over the lazy dog",
  "model": "sentence-transformers/all-MiniLM-L6-v2"  // optional, uses default if omitted
}
```

**Response:**
```json
{
  "text": "The quick brown fox jumps over the lazy dog",
  "embedding": [0.123, -0.456, 0.789, ...],  // 384-dimensional vector
  "model": "sentence-transformers/all-MiniLM-L6-v2",
  "dimension": 384
}
```

**Usage:**
```bash
curl -X POST 'http://localhost:8002/api/embed/' \
  -H 'Content-Type: application/json' \
  -d '{"text": "Machine learning is transforming technology"}'
```

**Error Responses:**
- `503`: Embedding service unavailable
- `500`: Internal server error

**Performance:**
- Typical latency: 50-200ms (depends on text length and service load)
- Maximum text length: 10,000 characters (enforced by embedding service)

---

### 2. Generate Batch Embeddings
**POST `/api/embed/batch`**

Generate embeddings for multiple texts in a single request. More efficient than calling the single endpoint multiple times.

**Request Body:**
```json
{
  "texts": [
    "First document to embed",
    "Second document to embed",
    "Third document to embed"
  ],
  "model": "sentence-transformers/all-MiniLM-L6-v2"  // optional
}
```

**Response:**
```json
{
  "embeddings": [
    {
      "text": "First document to embed",
      "embedding": [0.123, -0.456, ...],
      "model": "sentence-transformers/all-MiniLM-L6-v2",
      "dimension": 384
    },
    {
      "text": "Second document to embed",
      "embedding": [0.789, 0.234, ...],
      "model": "sentence-transformers/all-MiniLM-L6-v2",
      "dimension": 384
    },
    ...
  ],
  "model": "sentence-transformers/all-MiniLM-L6-v2",
  "dimension": 384
}
```

**Usage:**
```bash
curl -X POST 'http://localhost:8002/api/embed/batch' \
  -H 'Content-Type: application/json' \
  -d '{
    "texts": [
      "Natural language processing",
      "Computer vision",
      "Reinforcement learning"
    ]
  }'
```

**Constraints:**
- Minimum texts: 1
- Maximum texts: 100 (enforced by embedding service)
- Timeout: 60 seconds (longer than single embed due to batch processing)

**Error Responses:**
- `503`: Embedding service unavailable
- `500`: Internal server error
- `422`: Validation error (e.g., empty texts list)

**Performance:**
- Batch processing is ~5-10x faster than individual requests
- Typical latency: 200-500ms for 10 texts
- Recommended batch size: 10-50 texts for optimal performance

---

### 3. Compute Text Similarity
**POST `/api/embed/similarity`**

Compute cosine similarity between two text strings. Generates embeddings for both texts and calculates similarity score.

**Request Body:**
```json
{
  "text1": "Machine learning is AI",
  "text2": "Deep learning is machine learning",
  "model": "sentence-transformers/all-MiniLM-L6-v2"  // optional
}
```

**Response:**
```json
{
  "text1": "Machine learning is AI",
  "text2": "Deep learning is machine learning",
  "similarity": 0.87,  // score between -1 and 1
  "model": "sentence-transformers/all-MiniLM-L6-v2"
}
```

**Similarity Score Interpretation:**
- `1.0`: Identical or near-identical texts
- `0.8-0.99`: Very similar (high semantic overlap)
- `0.6-0.79`: Moderately similar (related topics)
- `0.4-0.59`: Somewhat similar (share some concepts)
- `0.2-0.39`: Weakly similar (distant relation)
- `0.0-0.19`: Dissimilar (unrelated topics)
- `< 0.0`: Opposite meaning (rare with typical text)

**Usage:**
```bash
curl -X POST 'http://localhost:8002/api/embed/similarity' \
  -H 'Content-Type: application/json' \
  -d '{
    "text1": "The cat sat on the mat",
    "text2": "A feline rested on the rug"
  }'
```

**Implementation Details:**
- Uses batch embedding endpoint (generates both embeddings in one call)
- Computes cosine similarity: `(A · B) / (||A|| ||B||)`
- Uses numpy for efficient vector operations

**Error Responses:**
- `503`: Embedding service unavailable
- `500`: Internal server error

**Performance:**
- Typical latency: 100-300ms (generates 2 embeddings + computation)

---

### 4. Get Embedding Configuration
**GET `/api/embed/config`**

Retrieve current embedding model configuration.

**Response:**
```json
{
  "model": "sentence-transformers/all-MiniLM-L6-v2",
  "provider": "huggingface",
  "dimension": 384,
  "description": "Fast, lightweight embeddings via sentence-transformers"
}
```

**Usage:**
```bash
curl -X GET 'http://localhost:8002/api/embed/config'
```

**Response Fields:**
- `model`: Current model identifier (HuggingFace model name)
- `provider`: Embedding provider (currently only "huggingface" supported)
- `dimension`: Vector dimensionality (384 for all-MiniLM-L6-v2)
- `description`: Human-readable model description

---

### 5. Update Embedding Configuration
**POST `/api/embed/config`**

Update the embedding model configuration. **Admin endpoint** - changes affect all subsequent embeddings.

**Query Parameters:**
- `provider` (required): Embedding provider (currently only "huggingface" supported)
- `model` (required): Model identifier (e.g., "sentence-transformers/all-MiniLM-L6-v2")
- `lock` (optional): Lock configuration to prevent further changes

**Response:**
```json
{
  "model": "sentence-transformers/all-mpnet-base-v2",
  "provider": "huggingface",
  "dimension": 384,
  "description": "Embedding model: sentence-transformers/all-mpnet-base-v2"
}
```

**Usage:**
```bash
# Update model
curl -X POST 'http://localhost:8002/api/embed/config?provider=huggingface&model=sentence-transformers/all-mpnet-base-v2'

# Update and lock
curl -X POST 'http://localhost:8002/api/embed/config?provider=huggingface&model=BAAI/bge-small-en-v1.5&lock=true'
```

**Supported Models:**
- `sentence-transformers/all-MiniLM-L6-v2` (default, fastest, 384 dims)
- `sentence-transformers/all-mpnet-base-v2` (better quality, 768 dims)
- `BAAI/bge-small-en-v1.5` (state-of-art small model, 384 dims)

**Error Responses:**
- `403`: Configuration is locked (cannot update)
- `400`: Invalid provider or model
- `503`: Embedding service unavailable
- `500`: Internal server error

**Behavior:**
- Configuration change requires embedding service restart to take effect
- Locked configuration cannot be updated (returns 403)
- Model must be available in HuggingFace model hub

---

## Integration Examples

### Python with requests
```python
import requests

# Single embedding
response = requests.post(
    "http://localhost:8002/api/embed/",
    json={"text": "Hello world"}
)
embedding = response.json()["embedding"]

# Batch embeddings
response = requests.post(
    "http://localhost:8002/api/embed/batch",
    json={"texts": ["Text 1", "Text 2", "Text 3"]}
)
embeddings = [item["embedding"] for item in response.json()["embeddings"]]

# Similarity
response = requests.post(
    "http://localhost:8002/api/embed/similarity",
    json={"text1": "cat", "text2": "dog"}
)
similarity_score = response.json()["similarity"]
```

### JavaScript/TypeScript with fetch
```javascript
// Single embedding
const response = await fetch('http://localhost:8002/api/embed/', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({text: 'Hello world'})
});
const {embedding} = await response.json();

// Batch embeddings
const batchResponse = await fetch('http://localhost:8002/api/embed/batch', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({texts: ['Text 1', 'Text 2']})
});
const {embeddings} = await batchResponse.json();

// Similarity
const simResponse = await fetch('http://localhost:8002/api/embed/similarity', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({text1: 'cat', text2: 'dog'})
});
const {similarity} = await simResponse.json();
```

### curl Examples
```bash
# Single embedding
curl -X POST http://localhost:8002/api/embed/ \
  -H 'Content-Type: application/json' \
  -d '{"text":"Hello world"}'

# Batch (using jq for formatting)
curl -X POST http://localhost:8002/api/embed/batch \
  -H 'Content-Type: application/json' \
  -d '{"texts":["Text 1","Text 2"]}' | jq '.embeddings[].embedding | length'

# Similarity
curl -X POST http://localhost:8002/api/embed/similarity \
  -H 'Content-Type: application/json' \
  -d '{"text1":"cat","text2":"dog"}' | jq '.similarity'
```

---

## Environment Variables

```bash
# Embedding service URL (required)
EMBEDDING_SERVICE_URL=http://localhost:8001

# Embedding service configuration (set on embedding service)
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_PROVIDER=huggingface
EMBEDDING_LOCK=false  # Set to true to lock configuration
```

---

## Error Handling

All endpoints use consistent error responses:

```json
{
  "detail": "Error message describing what went wrong"
}
```

**Common Error Status Codes:**
- `400`: Bad Request (validation error, invalid parameters)
- `403`: Forbidden (configuration locked)
- `422`: Unprocessable Entity (Pydantic validation error)
- `500`: Internal Server Error (unexpected error)
- `503`: Service Unavailable (embedding service not responding)

**Retry Logic Recommendations:**
- `503` errors: Retry with exponential backoff (service may be starting up)
- `500` errors: Retry once, then report error
- `400`, `403`, `422`: Do not retry (client error)

---

## Performance Optimization

### 1. Batch Processing
Always use `/embed/batch` for multiple texts:
```python
# ❌ Slow: Individual requests
embeddings = [
    requests.post(url, json={"text": t}).json()["embedding"]
    for t in texts
]

# ✅ Fast: Single batch request
response = requests.post(
    url + "/batch",
    json={"texts": texts}
)
embeddings = [e["embedding"] for e in response.json()["embeddings"]]
```

### 2. Connection Pooling
Reuse HTTP connections:
```python
import requests

# Create session with connection pooling
session = requests.Session()
session.headers.update({'Content-Type': 'application/json'})

# Reuse for multiple requests
for text in texts:
    response = session.post(url, json={"text": text})
```

### 3. Caching
Cache embeddings for frequently used texts:
```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_embedding(text: str):
    response = requests.post(url, json={"text": text})
    return tuple(response.json()["embedding"])
```

### 4. Async Processing
Use async HTTP clients for concurrent requests:
```python
import httpx
import asyncio

async def embed_many(texts: list[str]):
    async with httpx.AsyncClient() as client:
        tasks = [
            client.post(url, json={"text": t})
            for t in texts
        ]
        responses = await asyncio.gather(*tasks)
        return [r.json()["embedding"] for r in responses]
```

---

## Testing

### Unit Tests
```python
import pytest
from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)

def test_embed_single():
    response = client.post("/api/embed/", json={"text": "test"})
    assert response.status_code == 200
    data = response.json()
    assert "embedding" in data
    assert len(data["embedding"]) == 384

def test_embed_batch():
    response = client.post(
        "/api/embed/batch",
        json={"texts": ["test1", "test2"]}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["embeddings"]) == 2

def test_similarity():
    response = client.post(
        "/api/embed/similarity",
        json={"text1": "cat", "text2": "dog"}
    )
    assert response.status_code == 200
    assert "similarity" in response.json()
```

### Integration Tests
```bash
# Start embedding service
cd backend && uvicorn src.services.embedding.server:app --port 8001 &

# Start API gateway
cd backend && uvicorn src.api.main:app --port 8002 &

# Test endpoints
curl http://localhost:8002/api/embed/config
curl -X POST http://localhost:8002/api/embed/ \
  -H 'Content-Type: application/json' \
  -d '{"text":"test"}'

# Cleanup
pkill -f "uvicorn"
```

---

## Troubleshooting

### Embedding service not responding (503 error)
**Symptoms:** All endpoints return 503
**Causes:**
- Embedding service not running
- Wrong EMBEDDING_SERVICE_URL
- Network connectivity issues

**Solutions:**
```bash
# Check if service is running
curl http://localhost:8001/health

# Start embedding service
cd backend && uvicorn src.services.embedding.server:app --port 8001

# Verify environment variable
echo $EMBEDDING_SERVICE_URL

# Test connectivity
telnet localhost 8001
```

### Slow embedding generation
**Symptoms:** High latency (>1s per request)
**Causes:**
- Large batch sizes
- Model loading on first request
- CPU/memory constraints

**Solutions:**
- Use smaller batch sizes (10-50 texts)
- Warm up service with test request on startup
- Scale embedding service horizontally
- Use GPU acceleration if available
- Switch to smaller model (all-MiniLM-L6-v2)

### Configuration locked (403 error)
**Symptoms:** Cannot update embedding model
**Cause:** Configuration locked via lock=true

**Solution:**
```bash
# Option 1: Restart embedding service without lock
EMBEDDING_LOCK=false uvicorn src.services.embedding.server:app --port 8001

# Option 2: Edit selection.json file
rm backend/src/services/embedding/selection.json
# Restart service
```

### Dimension mismatch errors
**Symptoms:** Database insertion fails, vector search errors
**Cause:** Changed embedding model with different dimension

**Solution:**
```sql
-- Check current vectors
SELECT dimension(embedding) FROM document_chunks LIMIT 1;

-- If mismatch, re-generate all embeddings
-- (This is destructive - run in test environment first)
UPDATE document_chunks SET embedding = NULL, is_processed = FALSE;
-- Then re-process with new model
```

---

## Production Recommendations

1. **Service Redundancy**: Run multiple embedding service instances behind load balancer
2. **Monitoring**: Track latency, error rates, throughput with Prometheus/Grafana
3. **Caching**: Implement Redis cache for frequently embedded texts
4. **Rate Limiting**: Prevent abuse with rate limiting middleware
5. **Async Client**: Use httpx.AsyncClient in production for better concurrency
6. **Health Checks**: Monitor embedding service health from gateway
7. **Fallback**: Implement fallback to alternative provider on service failure
8. **Connection Pooling**: Use persistent connections to embedding service

---

## Future Enhancements

- [ ] Support for additional providers (OpenAI, Cohere, Vertex AI)
- [ ] Automatic model selection based on text language
- [ ] Embedding caching layer (Redis)
- [ ] Batch processing queue for large jobs
- [ ] GPU acceleration support
- [ ] Model auto-scaling based on load
- [ ] Prometheus metrics export
- [ ] Streaming response for large batches
- [ ] Multi-model ensemble embeddings
- [ ] Fine-tuned domain-specific models
