# Vecinita FastAPI Agent — build from repository root (dockerContext: .).
# Calls separate embedding service for embeddings — zero local embedding models.
# For scraping with Playwright, see apis/gateway/Dockerfile.scraper

# Build stage - install dependencies
FROM python:3.11-slim-bookworm AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
	build-essential \
	pkg-config && \
	rm -rf /var/lib/apt/lists/*

# Copy manifests first so this layer invalidates when pins change (uv.lock + pyproject stay in sync in CI).
# Installs still use the curated runtime list below (not full uv.lock export) to keep image size small for Render.
COPY apis/gateway/pyproject.toml apis/gateway/uv.lock ./

# Install dependencies to /install (NO EMBEDDING MODELS!)
# Embeddings handled by separate embedding service - saves ~50MB+ memory
RUN pip install --no-cache-dir --upgrade pip && \
	pip install --prefix=/install --no-cache-dir --retries 5 --default-timeout=1000 \
	fastapi uvicorn \
	langchain langchain-community langchain-core \
	langchain-openai langchain-groq langchain-tavily langchain-text-splitters \
	langchain-huggingface langgraph \
	psycopg2-binary \
	beautifulsoup4 pypdf \
	python-dotenv pydantic requests httpx langdetect tqdm \
	python-multipart \
	gotrue langchain-ollama langsmith ddgs \
	guardrails-ai \
	modal>=1.3.5

# Runtime stage - minimal image
FROM python:3.11-slim-bookworm AS runtime

WORKDIR /app

# Install only runtime dependencies (curl for healthcheck)
RUN apt-get update && apt-get install -y --no-install-recommends \
	curl && \
	rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Application source (canonical tree under apis/gateway/src; includes apis/agent via symlink)
COPY apis/gateway/src ./src/
COPY apis/gateway/scripts ./scripts/

# Python env flags
ENV PYTHONUNBUFFERED=1
ENV TF_ENABLE_ONEDNN_OPTS=0
ENV PORT=10000

# Expose the FastAPI port (uses PORT env var, default 10000 for Render)
EXPOSE ${PORT}

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=5 \
	CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

# Start the FastAPI app via uvicorn (module path: src.agent.main:app)
# Use PORT env var (default 8000 for local dev, 10000 for Render)
# Add graceful shutdown timeout to prevent hanging deploys
CMD ["sh", "-c", "uvicorn src.agent.main:app --host 0.0.0.0 --port ${PORT:-8000} --timeout-graceful-shutdown 30"]