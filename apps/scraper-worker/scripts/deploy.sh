#!/bin/bash
# Modal Deployment Script
# This script handles authentication and deployment to Modal

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}🚀 Vecinita Scraper - Modal Deployment${NC}"
echo "========================================"
echo ""

# Check if MODAL_TOKEN_ID and MODAL_TOKEN_SECRET are set
if [ -z "$MODAL_TOKEN_ID" ] && [ -z "$MODAL_TOKEN_SECRET" ]; then
    echo -e "${YELLOW}📋 Modal credentials not found in environment.${NC}"
    echo "   You have two options:"
    echo ""
    echo "   Option 1: Use existing Modal token"
    echo "   $ modal auth login"
    echo ""
    echo "   Option 2: Set environment variables"
    echo "   $ export MODAL_TOKEN_ID=your-token-id"
    echo "   $ export MODAL_TOKEN_SECRET=your-token-secret"
    echo ""
    echo "   Then run this script again."
    exit 1
fi

# Set PYTHONPATH
export PYTHONPATH=src

# Prefer Python 3.11+ for deployment (required by StrEnum usage)
PYTHON_BIN="${PYTHON_BIN:-python3.11}"
if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
    PYTHON_BIN="python3"
fi

echo -e "${GREEN}✓${NC} Using Python interpreter: $PYTHON_BIN"

# Load environment variables from .env
if [ -f .env ]; then
    echo -e "${GREEN}✓${NC} Loading environment from .env"
    set -a
    source .env
    set +a
else
    echo -e "${RED}✗${NC} .env file not found"
    echo "   Please create .env with required environment variables"
    exit 1
fi

# Verify required environment variables
echo ""
echo "🔍 Checking configuration..."

required_vars=(
    "DATABASE_URL"
    "EMBEDDING_UPSTREAM_URL"
)

missing_vars=()
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        missing_vars+=("$var")
    else
        echo -e "${GREEN}✓${NC} $var configured"
    fi
done

if [ ${#missing_vars[@]} -ne 0 ]; then
    echo ""
    echo -e "${RED}✗ Missing required environment variables:${NC}"
    for var in "${missing_vars[@]}"; do
        echo "   - $var"
    done
    echo ""
    echo "   Please set these in your .env file"
    exit 1
fi

# Run tests
echo ""
echo "🧪 Running tests..."
if ! "$PYTHON_BIN" -m pytest tests/unit tests/integration -q; then
    echo -e "${RED}✗${NC} Tests failed"
    exit 1
fi
echo -e "${GREEN}✓${NC} All tests passed"

# Deploy workers app
echo ""
echo "📦 Deploying workers app..."
if "$PYTHON_BIN" -m modal deploy src/vecinita_scraper/app.py; then
    echo -e "${GREEN}✓${NC} Workers app deployed"
else
    echo -e "${RED}✗${NC} Failed to deploy workers app"
    exit 1
fi

# Deploy API app
echo ""
echo "📦 Deploying API app..."
if "$PYTHON_BIN" -m modal deploy src/vecinita_scraper/api/app.py; then
    echo -e "${GREEN}✓${NC} API app deployed"
else
    echo -e "${RED}✗${NC} Failed to deploy API app"
    exit 1
fi

echo ""
echo -e "${GREEN}✅ Deployment successful!${NC}"
echo ""
echo "📊 Deployment Summary"
echo "==================="
echo "Workers app: https://modalpy.com/apps/vecinita-scraper"
echo "API app:     https://modalpy.com/apps/vecinita-scraper-api"
echo ""
echo "View logs: modal logs <app-name>"
echo "View status: modal status"
echo ""
