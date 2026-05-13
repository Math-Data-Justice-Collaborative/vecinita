# Vecinita Agent Service — standalone build from repository root (dockerContext: .).
# RAG brain: LlamaIndex pipeline, conversation, tool calling, vector search.
# No gateway code required — shared modules come from packages/.

FROM python:3.11-slim-bookworm AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
	build-essential \
	pkg-config && \
	rm -rf /var/lib/apt/lists/*

COPY apps/agent/pyproject.toml ./

RUN pip install --no-cache-dir --upgrade pip && \
	pip install --prefix=/install --no-cache-dir --retries 5 --default-timeout=1000 \
	fastapi uvicorn \
	langchain langchain-community langchain-core \
	langchain-openai langchain-groq langchain-tavily langchain-text-splitters \
	langchain-huggingface langgraph langgraph-checkpoint \
	psycopg2-binary \
	beautifulsoup4 pypdf \
	python-dotenv pydantic pydantic-settings requests httpx langdetect tqdm \
	python-multipart pyyaml \
	gotrue langchain-ollama langsmith ddgs \
	guardrails-ai \
	modal>=1.3.5

FROM python:3.11-slim-bookworm AS runtime

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
	curl && \
	rm -rf /var/lib/apt/lists/*

COPY --from=builder /install /usr/local

COPY packages/ ./packages/
RUN pip install --no-cache-dir -e ./packages/common -e ./packages/config -e ./packages/db

COPY apps/agent/src ./src/

ENV PYTHONUNBUFFERED=1
ENV TF_ENABLE_ONEDNN_OPTS=0
ENV PORT=10000

EXPOSE ${PORT}

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=5 \
	CMD curl -f http://localhost:${PORT:-8000}/agent/health || exit 1

CMD ["sh", "-c", "uvicorn src.agent.main:app --host 0.0.0.0 --port ${PORT:-8000} --timeout-graceful-shutdown 30"]
