#!/bin/bash
# Cron Job Scraper Wrapper
# This script is called by the Render cron service
# It runs the VECINA scraper in streaming mode with proper error handling

set -e  # Exit on error
set -o pipefail  # Exit if any pipe command fails

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=========================================="
echo "VECINA Cron Scraper Started"
echo "$(date '+%Y-%m-%d %H:%M:%S')"
echo "=========================================="

# Ensure we're in the correct directory
cd /app || { echo -e "${RED}❌ Failed to change to /app${NC}"; exit 1; }
echo -e "${GREEN}✓ Working directory: $(pwd)${NC}"

# Check required environment variables
echo ""
echo "Checking environment variables..."

MISSING_VARS=0

if [ -z "$SUPABASE_URL" ]; then
    echo -e "${RED}❌ ERROR: SUPABASE_URL not set${NC}"
    MISSING_VARS=$((MISSING_VARS + 1))
fi

if [ -z "$SUPABASE_KEY" ]; then
    echo -e "${RED}❌ ERROR: SUPABASE_KEY not set${NC}"
    MISSING_VARS=$((MISSING_VARS + 1))
fi

if [ -z "$DATABASE_URL" ]; then
    echo -e "${YELLOW}⚠ WARNING: DATABASE_URL not set${NC}"
    echo "  Attempting to use SUPABASE_URL for database connection..."
fi

if [ $MISSING_VARS -gt 0 ]; then
    echo -e "${RED}❌ Missing $MISSING_VARS required environment variable(s)${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Environment variables validated${NC}"

# Check critical files exist
echo ""
echo "Checking data files..."

if [ ! -f "data/urls.txt" ]; then
    echo -e "${RED}❌ ERROR: data/urls.txt not found${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Found data/urls.txt${NC}"

if [ ! -d "data/config" ]; then
    echo -e "${YELLOW}⚠ WARNING: data/config directory not found (scraper may use defaults)${NC}"
else
    echo -e "${GREEN}✓ Found data/config directory${NC}"
fi

# Create required directories
mkdir -p data/output logs
echo -e "${GREEN}✓ Output directories ready${NC}"

# Run the scraper with streaming mode
# --stream: Upload chunks immediately to Supabase (memory efficient for cron)
# --no-confirm: Skip confirmation prompts
# --verbose: Show detailed logs for debugging
echo ""
echo "Starting scraper (streaming mode)..."
echo "=========================================="
python -m src.scraper.cli --stream --no-confirm --verbose

SCRAPER_EXIT_CODE=$?

echo "=========================================="

if [ $SCRAPER_EXIT_CODE -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✅ Scraper completed successfully${NC}"
    echo "Completed at: $(date '+%Y-%m-%d %H:%M:%S')"
    echo ""
else
    echo ""
    echo -e "${RED}❌ Scraper failed with exit code: $SCRAPER_EXIT_CODE${NC}"
    echo "Failed at: $(date '+%Y-%m-%d %H:%M:%S')"
    echo ""
    exit $SCRAPER_EXIT_CODE
fi
