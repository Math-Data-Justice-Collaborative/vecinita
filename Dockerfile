# ############################################################################
# FILE: Dockerfile
# PATH: /mnt/data_prod/vecinita/Dockerfile
# ROLE: High-Fidelity Gemini Engine Environment
# ############################################################################

# Use official Playwright Python image as the base
FROM mcr.microsoft.com/playwright/python:v1.49.0-jammy

# Set the working directory in the container
WORKDIR /app

# Copy pyproject.toml and README.md for dependency installation
COPY pyproject.toml README.md ./

# Copy source code needed for package installation
COPY src/ ./src/

# Copy the data directory for internal resource files
COPY data/ ./data/

# Install system dependencies required for building packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    graphviz \
    graphviz-dev \
    pkg-config

# Environment configurations
ENV PYTHONUNBUFFERED=1
ENV TF_ENABLE_ONEDNN_OPTS=0

# Upgrade pip and install package dependencies from pyproject.toml
RUN pip install --no-cache-dir --upgrade pip

RUN pip install --no-cache-dir --retries 5 --default-timeout=1000 ".[embedding]"

# SURGICAL INJECTION: Install Gemini and LangDetect libraries
# This bypasses pyproject.toml to fix the ModuleNotFoundError immediately
# now in the pyproject.toml
#RUN pip install --no-cache-dir langchain-google-genai==1.0.10 langdetect==1.0.9

# Clean up apt cache to keep the image slim
RUN rm -rf /var/lib/apt/lists/*

# Pre-cache the SentenceTransformer model
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')" || true

# Ensure Playwright browsers are installed
RUN playwright install --with-deps

# Expose the application port
EXPOSE 8080

# Command to run the Gemini-powered FastAPI application
CMD ["uvicorn", "src.agent.main:app", "--host", "0.0.0.0", "--port", "8080"]

## end-of-file Dockerfile
