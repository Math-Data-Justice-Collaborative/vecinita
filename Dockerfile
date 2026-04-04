# Root Dockerfile for Render services that default to repo-root Dockerfile path.
# Builds the gateway app from backend sources while keeping the Render service
# configuration simple when dockerfilePath cannot be customized.

FROM python:3.11-slim-bookworm AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
	build-essential \
	pkg-config && \
	rm -rf /var/lib/apt/lists/*

COPY backend/pyproject.toml ./pyproject.toml

RUN pip install --no-cache-dir --upgrade pip && \
	pip install --prefix=/install --no-cache-dir --retries 5 --default-timeout=1000 \
	fastapi uvicorn \
	langchain langchain-community langchain-core \
	langchain-openai langchain-groq langchain-tavily langchain-text-splitters \
	langchain-huggingface langgraph \
	supabase chromadb psycopg2-binary \
	beautifulsoup4 pypdf \
	python-dotenv pydantic requests httpx langdetect tqdm \
	python-multipart \
	gotrue langchain-ollama langsmith ddgs \
	guardrails-ai

FROM python:3.11-slim-bookworm AS runtime

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
	curl && \
	rm -rf /var/lib/apt/lists/*

COPY --from=builder /install /usr/local
COPY backend/src/ ./src/
COPY backend/scripts/ ./scripts/

ENV PYTHONUNBUFFERED=1
ENV TF_ENABLE_ONEDNN_OPTS=0
ENV PORT=10000

EXPOSE ${PORT}

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=5 \
	CMD curl -f http://localhost:${PORT:-10000}/health || exit 1

CMD ["sh", "-c", "uvicorn src.api.main:app --host 0.0.0.0 --port ${PORT:-10000} --timeout-graceful-shutdown 30"]