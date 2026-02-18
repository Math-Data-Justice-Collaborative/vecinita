# Embedding Service Architecture

## Overview

Vecinita uses a **microservice architecture** for text embeddings to optimize memory usage and enable horizontal scaling. The embedding service runs as a separate lightweight FastAPI service that generates vector embeddings for text using sentence-transformers.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     EMBEDDING SERVICE                        │
│  (vecinita-embedding:8001 - Free Tier Render Service)      │
│                                                               │
│  • FastAPI server on port 8001                               │
│  • sentence-transformers/all-MiniLM-L6-v2                   │
│  • 384-dimensional vectors                                   │
│  • Endpoints: /embed, /embed-batch, /health                  │
│  • HuggingFace cache: /tmp/huggingface_cache                │
└───────────────────┬─────────────────────────────────────────┘
                    │
                    │ HTTP Requests (Internal Network)
                    │
        ┌───────────┴────────────┐
        │                        │
        ▼                        ▼
┌───────────────┐        ┌───────────────┐
│  AGENT        │        │  SCRAPER      │
│  SERVICE      │        │  SERVICE      │
│  (port 10000) │        │  (cron)       │
│               │        │               │
│ Uses:         │        │ Uses:         │
│ ✅ Service    │        │ ⚠️  Local    │
│ (primary)     │        │ (default)     │
│               │        │               │
│ Fallback:     │        │ Fallback:     │
│ FastEmbed     │        │ Service →     │
│ HuggingFace   │        │ FastEmbed →   │
│               │        │ HuggingFace   │
└───────────────┘        └───────────────┘
```

## Service Connections

### 1. Agent Service → Embedding Service

**Primary Connection Method**: HTTP Client

```python
# backend/src/agent/main.py (lines 111-122)
embedding_service_url = os.environ.get(
    "EMBEDDING_SERVICE_URL", "http://embedding-service:8001"
)
from src.embedding_service.client import create_embedding_client
embedding_model = create_embedding_client(embedding_service_url)
```

**Environment Variables**:
- `EMBEDDING_SERVICE_URL`: `http://vecinita-embedding:8001` (Render private network)
- Docker: `http://embedding-service:8001` (Docker internal network)

**Fallback Chain**:
1. **Embedding Service** (primary, lightweight)
2. **FastEmbed** (local, fast-bge-small-en-v1.5)
3. **HuggingFace** (local, all-MiniLM-L6-v2)

### 2. Scraper Service → Embedding Service

**Primary Connection Method**: Local Embeddings (Default)

```python
# backend/src/scraper/uploader.py (lines 51-90)
# Scraper defaults to use_local_embeddings=True
embedding_service_url = os.getenv(
    "EMBEDDING_SERVICE_URL", "http://embedding-service:8001"
)
# Tries: Service → FastEmbed → HuggingFace
```

**Why Local Embeddings?**
- Scraper runs as **cron job** (not long-running service)
- Loads ~200MB of embedding model into memory once
- Processes batches efficiently without network overhead
- Embedding service may spin down on free tier between scraper runs

**Environment Variables**:
- `EMBEDDING_SERVICE_URL`: Set but not primary (fallback option)
- `SUPABASE_URL`, `SUPABASE_KEY`: Required for database upload

**Fallback Chain**:
1. **FastEmbed** (primary, local)
2. **HuggingFace** (fallback, local)
3. **Embedding Service** (available if needed)

## Deployment Configuration

### Render.yaml Configuration

```yaml
# Embedding Service (Free Tier)
services:
  - type: web
    name: vecinita-embedding
    runtime: docker
    plan: free
    dockerfilePath: ./backend/Dockerfile.embedding
    envVars:
      - key: PORT
        value: "8001"
      - key: HF_HOME
        value: "/tmp/huggingface_cache"

# Agent Service (Free Tier)
  - type: web
    name: vecinita-agent
    envVars:
      - key: EMBEDDING_SERVICE_URL
        value: "http://vecinita-embedding:8001"  # Private network

# Scraper Service (Cron Job)
  - type: cron
    name: vecinita-scraper
    envVars:
      - key: EMBEDDING_SERVICE_URL
        value: "http://vecinita-embedding:8001"  # Available but not primary
```

### Docker Compose Configuration

```yaml
services:
  embedding-service:
    image: vecinita-embedding:latest
    ports:
      - "8001:8001"
    environment:
      PORT: "8001"
      HF_HOME: /tmp/huggingface_cache

  vecinita-agent:
    depends_on:
      embedding-service:
        condition: service_healthy
    environment:
      EMBEDDING_SERVICE_URL: "http://embedding-service:8001"

  # vecinita-scraper (optional - uses local embeddings)
  #   depends_on:
  #     embedding-service:
  #       condition: service_healthy
  #   environment:
  #     EMBEDDING_SERVICE_URL: "http://embedding-service:8001"
```

## Client Implementation

### EmbeddingServiceClient

**Location**: [backend/src/embedding_service/client.py](../backend/src/embedding_service/client.py)

**Features**:
- LangChain-compatible `Embeddings` interface
- HTTP client using `httpx` library
- Timeout: 30 seconds (configurable)
- Endpoints: `/embed` (single), `/embed-batch` (multiple)

**Usage**:
```python
from src.embedding_service.client import create_embedding_client

# Create client
client = create_embedding_client("http://vecinita-embedding:8001")

# Embed single query
vector = client.embed_query("What is SNAP?")  # Returns List[float]

# Embed multiple documents (batch)
vectors = client.embed_documents([
    "Document 1 text",
    "Document 2 text"
])  # Returns List[List[float]]
```

## Health Checks

All services include health check endpoints:

### Embedding Service
```bash
curl http://vecinita-embedding:8001/health
# Response: {"status": "healthy", "model": "all-MiniLM-L6-v2"}
```

### Agent Service
```bash
curl http://vecinita-agent:10000/health
# Response: {"status": "healthy", "embedding_service": "connected"}
```

## Troubleshooting

### Agent: "Embedding service unreachable"

**Symptoms**: Agent logs show embedding service connection failures

**Causes**:
1. Embedding service not running or unhealthy
2. Incorrect `EMBEDDING_SERVICE_URL` environment variable
3. Network connectivity issues

**Solutions**:
```bash
# Check embedding service health
curl https://vecinita-embedding.onrender.com/health

# Verify agent has correct EMBEDDING_SERVICE_URL
# Render Dashboard → vecinita-agent → Environment
# Should be: http://vecinita-embedding:8001 (private network)

# Check agent logs for fallback behavior
# Agent should automatically fallback to FastEmbed/HuggingFace
```

### Scraper: Embedding Timeout

**Symptoms**: Scraper logs show "Embedding model initialization timeout"

**Causes**:
1. HuggingFace model download timeout
2. Insufficient memory for local embeddings

**Solutions**:
```bash
# Scraper uses local embeddings by default (no service dependency)
# Check scraper logs for model download progress
# HuggingFace models cached in /tmp/huggingface_cache

# If timeout persists, increase memory or use embedding service:
# Set use_local_embeddings=False in uploader initialization
```

### Docker: Service Not Found

**Symptoms**: `curl: (6) Could not resolve host: embedding-service`

**Causes**:
1. Docker containers not on same network
2. Service name mismatch

**Solutions**:
```bash
# Verify containers are running
docker ps | grep embedding

# Check Docker network
docker network inspect vecinita_default

# Restart with docker-compose
docker-compose down
docker-compose up -d
```

## Performance Metrics

### Embedding Service (Free Tier)

- **Model**: sentence-transformers/all-MiniLM-L6-v2
- **Vector Dimensions**: 384
- **Model Size**: ~80MB (cached)
- **Memory Usage**: ~200MB (loaded)
- **Latency**: 
  - Single embed: ~50-100ms
  - Batch (10): ~200-500ms
- **Cold Start**: 15-20 seconds (model download)

### Agent Service (with Embedding Service)

- **Memory Savings**: ~150MB (no local embedding model)
- **Startup Time**: 5-10 seconds (no model download)
- **Query Latency**: +50ms (network overhead)

### Scraper Service (local embeddings)

- **Memory Usage**: ~400MB (includes Playwright + embeddings)
- **Startup Time**: 10-15 seconds (model download)
- **Batch Processing**: 100 chunks in ~5-10 seconds

## Migration Guide

### From Local Embeddings → Embedding Service

**Agent** (already using service):
```python
# No changes needed - already configured
embedding_service_url = os.environ.get("EMBEDDING_SERVICE_URL")
embedding_model = create_embedding_client(embedding_service_url)
```

**Scraper** (if needed):
```python
# backend/src/scraper/uploader.py
# Change: use_local_embeddings=True
# To:     use_local_embeddings=False

uploader = DatabaseUploader(use_local_embeddings=False)
# Will use OpenAI embeddings (requires OPENAI_API_KEY)
```

### From Embedding Service → Local Embeddings

**Agent**:
```python
# backend/src/agent/main.py
# Remove embedding service initialization
# Use fallback directly:
from langchain_community.embeddings import FastEmbedEmbeddings
embedding_model = FastEmbedEmbeddings(model_name="fast-bge-small-en-v1.5")
```

## Best Practices

1. **Agent Service**: Always use embedding service (primary) with fallback chain
2. **Scraper Service**: Use local embeddings (default) for cron jobs
3. **Health Checks**: Monitor `/health` endpoint regularly
4. **Network**: Use private network addresses (http://service-name:port)
5. **Caching**: Set `HF_HOME=/tmp/huggingface_cache` for model persistence
6. **Timeouts**: Configure httpx timeout based on batch size (default: 30s)
7. **Fallbacks**: Always have multiple fallback options (Service → FastEmbed → HuggingFace)

## Related Documentation

- [Architecture Overview](ARCHITECTURE_MICROSERVICE.md)
- [Deployment Guide](../deployment/RENDER_DEPLOYMENT_THREE_SERVICES.md)
- [Quick Reference](QUICK_REFERENCE_MICROSERVICE.md)
- [Embedding Service Source](../backend/src/embedding_service/)
- [Embedding Client](../backend/src/embedding_service/client.py)
