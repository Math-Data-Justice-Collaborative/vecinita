# Embedding Service - Lightweight Microservice

A lightweight FastAPI service that provides text embeddings using `sentence-transformers/all-MiniLM-L6-v2`.

## Overview

This service is designed to run as an **independent Render free-tier service** (512MB), providing embeddings for:
- The agent service (FastAPI Q&A)
- The scraper service (background content processing)
- Any other service that needs text embeddings

## Features

- ✅ FastAPI service (high performance)
- ✅ Batch embedding support (efficient)
- ✅ Health check endpoint
- ✅ Similarity search (bonus feature)
- ✅ Lightweight (~350-400MB memory)
- ✅ Docker-optimized (multi-stage build)
- ✅ Production-ready

## Quick Start

### Local Development

```bash
# Install dependencies
cd backend
pip install -e ".[embedding]"

# Run service
python -m uvicorn src.embedding_service.main:app --reload --port 8001

# Test
curl http://localhost:8001/health
curl -X POST http://localhost:8001/embed \
  -H "Content-Type: application/json" \
  -d '{"text": "hello world"}'
```

### Docker

```bash
# Build
docker build -f Dockerfile.embedding -t vecinita-embedding .

# Run
docker run -p 8001:8001 -e PORT=8001 vecinita-embedding

# Test
curl http://localhost:8001/health
```

## API Endpoints

### Health Check

```http
GET /health
```

**Response:**
```json
{
  "status": "ok",
  "service": "embedding"
}
```

### Single Embedding

```http
POST /embed
Content-Type: application/json

{
  "text": "This is a sample text"
}
```

**Response:**
```json
{
  "embedding": [0.123, -0.456, ..., 384-dimensional vector],
  "dimension": 384,
  "model": "sentence-transformers/all-MiniLM-L6-v2"
}
```

### Batch Embeddings

```http
POST /embed-batch
Content-Type: application/json

{
  "texts": [
    "First text",
    "Second text",
    "Third text"
  ]
}
```

**Response:**
```json
{
  "embeddings": [
    [0.123, -0.456, ..., 384-dim],
    [0.789, 0.012, ..., 384-dim],
    [0.345, 0.678, ..., 384-dim]
  ],
  "dimension": 384,
  "count": 3,
  "model": "sentence-transformers/all-MiniLM-L6-v2"
}
```

### Similarity Search

```http
POST /similarity
Content-Type: application/json

{
  "query_request": {
    "text": "What is machine learning?"
  },
  "texts_request": {
    "texts": [
      "Machine learning is a subset of AI",
      "Python is a programming language",
      "Deep learning uses neural networks"
    ]
  }
}
```

**Response:**
```json
{
  "query": "What is machine learning?",
  "results": [
    {
      "text": "Machine learning is a subset of AI",
      "similarity": 0.95
    },
    {
      "text": "Deep learning uses neural networks",
      "similarity": 0.72
    },
    {
      "text": "Python is a programming language",
      "similarity": 0.15
    }
  ]
}
```

### Service Info

```http
GET /
```

**Response:**
```json
{
  "name": "Vecinita Embedding Service",
  "version": "0.1.0",
  "model": "sentence-transformers/all-MiniLM-L6-v2",
  "endpoints": {
    "health": "GET /health",
    "embed_single": "POST /embed",
    "embed_batch": "POST /embed-batch",
    "similarity": "POST /similarity"
  }
}
```

## Using from Agent Service

### Python Client

```python
from src.embedding_service.client import create_embedding_client

# Initialize (remote service)
client = create_embedding_client("http://embedding-service:8001")

# Single embedding
embedding = client.embed_query("hello world")
print(embedding)  # List of 384 floats

# Batch embeddings
embeddings = client.embed_documents([
    "First document",
    "Second document",
    "Third document"
])
print(embeddings)  # List of 3 embedding vectors
```

### Direct HTTP Calls

```bash
# Single embedding
curl -X POST http://embedding-service:8001/embed \
  -H "Content-Type: application/json" \
  -d '{"text": "hello"}'

# Batch embeddings
curl -X POST http://embedding-service:8001/embed-batch \
  -H "Content-Type: application/json" \
  -d '{"texts": ["hello", "world"]}'
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | 8001 | Port to listen on |
| `PYTHONUNBUFFERED` | 1 | Unbuffered Python output |
| `HF_HOME` | `/tmp/huggingface_cache` | HuggingFace cache directory |

## Performance

### Cold Start
- First request: ~20-30 seconds (downloads and caches model)
- Subsequent requests: ~100-300ms

### Throughput
- Single embedding: 1-5ms (cached model)
- Batch (100 texts): ~50-100ms (parallelized)

### Memory
- Idle: ~100-150MB
- With model loaded: ~350-400MB
- Fits comfortably in Render free tier (512MB)

## Model Details

**Model:** `sentence-transformers/all-MiniLM-L6-v2`
- **Dimension:** 384
- **Performance:** Very fast, lightweight
- **Use case:** Excellent for semantic search & clustering
- **Size:** ~50MB (downloaded on first use)
- **License:** Apache 2.0

See: https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2

## Deployment

### Local Docker Compose

```yaml
services:
  embedding-service:
    build:
      context: ./backend
      dockerfile: Dockerfile.embedding
    ports:
      - "8001:8001"
    environment:
      PORT: "8001"
      PYTHONUNBUFFERED: "1"
```

### Render

1. New Web Service
2. **Name:** `vecinita-embedding`
3. **Dockerfile:** `backend/Dockerfile.embedding`
4. **Plan:** Free
5. **Region:** Virginia
6. **Environment:**
   ```
   PORT=8001
   PYTHONUNBUFFERED=1
   ```

See full guide: `docs/RENDER_DEPLOYMENT_THREE_SERVICES.md`

## Monitoring

### Health Check

```bash
curl https://vecinita-embedding.onrender.com/health
```

### Logs

```bash
# Local
docker logs vecinita-embedding

# Render Dashboard
https://dashboard.render.com → Service → Logs
```

### Metrics to Monitor

- Response time (should be < 300ms)
- Memory usage (should stay < 450MB)
- Error rate (should be 0%)
- Uptime (should be > 99.9%)

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Model not found" | First request takes ~30s to download model |
| "Out of memory" | Service needs 512MB, check Render plan |
| "Slow responses" | Normal on cold start, should improve after |
| "Connection refused" | Service not running, check logs |

## API Error Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 422 | Validation error (bad input) |
| 500 | Server error (check logs) |

Example error response:
```json
{
  "detail": "String should have at most 10000 characters"
}
```

## Dependencies

### Production
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `pydantic` - Data validation
- `sentence-transformers` - Embedding model
- `numpy` - Numerical operations
- `scikit-learn` - Similarity computations

### Development
- All above + testing frameworks

## Contributing

To improve the embedding service:

1. Edit `src/embedding_service/main.py`
2. Test locally: `python -m uvicorn src.embedding_service.main:app --reload`
3. Test in Docker: `docker build -f Dockerfile.embedding .`
4. Deploy to Render

## License

Same as Vecinita (MIT)

## Support

- **API Docs:** http://localhost:8001/docs (Swagger UI)
- **Alt Docs:** http://localhost:8001/redoc (ReDoc)
- **Source:** `backend/src/embedding_service/main.py`
- **Client:** `backend/src/embedding_service/client.py`
