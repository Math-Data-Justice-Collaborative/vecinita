#!/usr/bin/env bash
set -euo pipefail

# Deploy embedding service to Cloud Run via gcloud CLI and print URL/env hints.
# Required env:
#   PROJECT_ID (or GCP_PROJECT_ID)
# Optional env:
#   REGION=us-central1
#   SERVICE_NAME=vecinita-embed

PROJECT_ID="${PROJECT_ID:-${GCP_PROJECT_ID:-}}"
REGION="${REGION:-${GCP_REGION:-us-central1}}"
SERVICE_NAME="${SERVICE_NAME:-vecinita-embed}"
AR_REPOSITORY="${AR_REPOSITORY:-vecinita}"

if [[ -z "${PROJECT_ID}" ]]; then
  echo "PROJECT_ID (or GCP_PROJECT_ID) is required" >&2
  exit 1
fi

if [[ "${PROJECT_ID}" =~ ^[0-9]+$ ]]; then
  PROJECT_ID="$(gcloud projects describe "${PROJECT_ID}" --format='value(projectId)')"
  if [[ -z "${PROJECT_ID}" ]]; then
    echo "Unable to resolve numeric project to project ID" >&2
    exit 1
  fi
fi

if ! command -v gcloud >/dev/null 2>&1; then
  echo "gcloud CLI not found. Install Google Cloud SDK first." >&2
  exit 1
fi

if ! gcloud auth list --format='value(account)' | grep -q .; then
  echo "No active gcloud account found. Run: gcloud auth login" >&2
  exit 1
fi

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
AR_HOST="${REGION}-docker.pkg.dev"
IMAGE="${AR_HOST}/${PROJECT_ID}/${AR_REPOSITORY}/${SERVICE_NAME}:latest"

use_source_deploy=false

echo "Ensuring Artifact Registry repository exists: ${AR_REPOSITORY}"
if ! gcloud artifacts repositories describe "${AR_REPOSITORY}" \
  --location="${REGION}" \
  --project="${PROJECT_ID}" >/dev/null 2>&1; then
  if ! gcloud artifacts repositories create "${AR_REPOSITORY}" \
    --repository-format=docker \
    --location="${REGION}" \
    --description="Vecinita Docker images" \
    --project="${PROJECT_ID}" \
    --quiet; then
    echo "Artifact Registry create denied; falling back to Cloud Run source deployment."
    use_source_deploy=true
  fi
fi

if [[ "${use_source_deploy}" == "false" ]]; then
  echo "Configuring docker auth for Artifact Registry: ${AR_HOST}"
  gcloud auth configure-docker "${AR_HOST}" --quiet >/dev/null

  echo "Building embedding image: ${IMAGE}"
  docker build -t "${IMAGE}" -f "${REPO_ROOT}/backend/Dockerfile.embedding" "${REPO_ROOT}/backend"

  echo "Pushing image: ${IMAGE}"
  docker push "${IMAGE}"

  echo "Deploying Cloud Run service: ${SERVICE_NAME} (${REGION})"
  gcloud run deploy "${SERVICE_NAME}" \
    --image="${IMAGE}" \
    --region="${REGION}" \
    --platform=managed \
    --memory=2Gi \
    --cpu=2 \
    --concurrency=80 \
    --min-instances=0 \
    --max-instances=10 \
    --timeout=60 \
    --allow-unauthenticated \
    --set-env-vars="EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2" \
    --project="${PROJECT_ID}" \
    --quiet
else
  echo "Deploying Cloud Run service from source: ${SERVICE_NAME} (${REGION})"
  gcloud run deploy "${SERVICE_NAME}" \
    --source="${REPO_ROOT}/backend" \
    --region="${REGION}" \
    --platform=managed \
    --allow-unauthenticated \
    --set-env-vars="EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2" \
    --project="${PROJECT_ID}" \
    --quiet
fi

SERVICE_URL="$(gcloud run services describe "${SERVICE_NAME}" --region "${REGION}" --project "${PROJECT_ID}" --format='value(status.url)')"

echo ""
echo "Embedding service deployed"
echo "Service URL: ${SERVICE_URL}"
if [[ "${use_source_deploy}" == "false" ]]; then
  echo "Artifact Registry image: ${IMAGE}"
else
  echo "Deploy mode: Cloud Run source build"
fi
echo ""
echo "Set these in backend/.env:"
echo "EMBEDDING_SERVICE_URL=${SERVICE_URL}"
echo "EMBEDDING_CLOUD_RUN_SERVICE=${SERVICE_NAME}"
echo "GCP_PROJECT_ID=${PROJECT_ID}"
echo "GCP_REGION=${REGION}"
