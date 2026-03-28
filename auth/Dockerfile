FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

# Copy project files
COPY pyproject.toml README.md ./

# Install dependencies using uv (auth proxy has minimal deps)
RUN /root/.local/bin/uv pip install --system --no-cache -e .

# Copy source code
COPY src/ src/

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8003/health')" || exit 1

# Run the app
CMD ["python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8003"]
