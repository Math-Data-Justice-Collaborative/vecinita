#!/usr/bin/env bash
# deploy/gcp/cloudrun-embed.sh
# ─────────────────────────────────────────────────────────────────────────────
# Deploy the embedding service to Google Cloud Run (serverless, scales to zero).
#
# The embedding service runs all-MiniLM-L6-v2 locally inside the container —
# no external API calls, no OpenAI. The model is baked into the Docker image
# on first build via the Dockerfile.embedding.
#
# Usage:
#   export PROJECT_ID=your-gcp-project
#   export REGION=us-central1
#   bash deploy/gcp/cloudrun-embed.sh
#
# Prerequisites:
#   gcloud auth login && gcloud auth configure-docker
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

PROJECT_ID="${PROJECT_ID:?Set PROJECT_ID environment variable}"
REGION="${REGION:-us-central1}"
SERVICE_NAME="vecinita-embed"
IMAGE="gcr.io/$PROJECT_ID/$SERVICE_NAME"

# Repo root (two levels above this script)
REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"

echo "==> Building embedding service Docker image…"
docker build \
  -t "$IMAGE:latest" \
  -f "$REPO_ROOT/backend/Dockerfile.embedding" \
  "$REPO_ROOT/backend"

echo "==> Pushing image to Google Container Registry…"
docker push "$IMAGE:latest"

echo "==> Deploying to Cloud Run ($REGION)…"
gcloud run deploy "$SERVICE_NAME" \
  --image="$IMAGE:latest" \
  --region="$REGION" \
  --platform=managed \
  --memory=2Gi \
  --cpu=2 \
  --concurrency=80 \
  --min-instances=0 \
  --max-instances=10 \
  --timeout=60 \
  --allow-unauthenticated \
  --set-env-vars="EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2" \
  --project="$PROJECT_ID"

# Capture the service URL and print instructions
SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" \
  --region="$REGION" \
  --project="$PROJECT_ID" \
  --format="value(status.url)")

echo ""
echo "==> Embedding service deployed!"
echo "    URL: $SERVICE_URL"
echo ""
echo "    Add this to your backend/.env on the Compute Engine VM:"
echo "    EMBEDDING_SERVICE_URL=$SERVICE_URL"
echo ""
echo "    Test with:"
echo "    curl -X POST $SERVICE_URL/embed \\"
echo "      -H 'Content-Type: application/json' \\"
echo "      -d '{\"text\": \"hello world\"}'"
