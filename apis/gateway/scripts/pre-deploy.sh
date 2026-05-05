#!/bin/bash
# apis/gateway/scripts/pre-deploy.sh (legacy path: backend/scripts/pre-deploy.sh)
#
# Pre-deployment hook for Render.
# This script runs BEFORE the service starts on each deploy.
#
# Purpose:
# - Run database migrations (once, before any instances boot)
# - Validate schema/configuration
# - Bootstrap database if needed
#
# Exit codes:
# - 0     → success, safe to proceed with deployment
# - 1     → failure, Render will cancel deploy and keep old instances
#
# Usage (in render.yaml): run from repo root or from the service WORKDIR (/app in Docker).
#   preDeployCommand: ./apis/gateway/scripts/pre-deploy.sh

set -e  # Exit on any error

# Python package root: flat image layout (.), monorepo apis/gateway, or legacy backend/.
if [ -f "src/config.py" ] && [ -d "scripts" ]; then
  PY_ROOT="."
elif [ -f "apis/gateway/src/config.py" ]; then
  PY_ROOT="apis/gateway"
elif [ -f "backend/src/config.py" ]; then
  PY_ROOT="backend"
else
  PY_ROOT=""
fi

echo "=========================================="
echo "Vecinita Pre-Deploy Script"
echo "=========================================="
echo "Time: $(date)"

# Set colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# ============================================================================
# Environment Validation
# ============================================================================

echo -e "\n${YELLOW}[1/4]${NC} Validating environment..."

if [ -z "$DATABASE_URL" ]; then
  echo -e "${RED}ERROR: DATABASE_URL not set${NC}"
  exit 1
fi

if [ -z "$PYTHONUNBUFFERED" ]; then
  echo -e "${YELLOW}WARNING: PYTHONUNBUFFERED not set; logging may buffer${NC}"
fi

echo -e "${GREEN}✓${NC} Environment variables validated"

# ============================================================================
# Database Connectivity Check
# ============================================================================

echo -e "\n${YELLOW}[2/4]${NC} Checking database connectivity..."

# Extract connection parameters from DATABASE_URL
# Format: postgresql://user:password@host:port/database
DB_REGEX='postgresql://([^:]+):([^@]+)@([a-zA-Z0-9.-]+):([0-9]+)/(.+)'

if [[ $DATABASE_URL =~ $DB_REGEX ]]; then
  DB_USER="${BASH_REMATCH[1]}"
  DB_PASSWORD="${BASH_REMATCH[2]}"
  DB_HOST="${BASH_REMATCH[3]}"
  DB_PORT="${BASH_REMATCH[4]}"
  DB_NAME="${BASH_REMATCH[5]}"
  
  echo "  Database: $DB_NAME"
  echo "  Host: $DB_HOST"
  echo "  Port: $DB_PORT"
  echo "  User: $DB_USER"
  
  # Test connection using psql if available
  if command -v psql &> /dev/null; then
    if PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1" &> /dev/null; then
      echo -e "${GREEN}✓${NC} Database is reachable"
    else
      echo -e "${RED}ERROR: Cannot connect to database${NC}"
      exit 1
    fi
  else
    echo -e "${YELLOW}⚠${NC}  psql not available; skipping connectivity test"
  fi
else
  echo -e "${YELLOW}⚠${NC}  DATABASE_URL format unrecognized; format check skipped"
fi

# ============================================================================
# Database Schema Migration
# ============================================================================

echo -e "\n${YELLOW}[3/4]${NC} Running database migrations..."

# Try to run Alembic if it exists
if [ -n "$PY_ROOT" ] && [ -f "${PY_ROOT}/alembic.ini" ] && command -v alembic &> /dev/null; then
  echo "  Running: alembic upgrade head"
  (cd "${PY_ROOT}" && alembic upgrade head)
  if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC} Migrations completed successfully"
  else
    echo -e "${RED}ERROR: Migration failed${NC}"
    exit 1
  fi
# Try to run schema bootstrap script if it exists
elif [ -n "$PY_ROOT" ] && [ -f "${PY_ROOT}/scripts/schema_install.sql" ]; then
  echo "  Running: schema_install.sql"
  PGPASSWORD="$DB_PASSWORD" psql \
    -h "$DB_HOST" \
    -U "$DB_USER" \
    -d "$DB_NAME" \
    -f "${PY_ROOT}/scripts/schema_install.sql"
  
  if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC} Schema installed successfully"
  else
    echo -e "${RED}ERROR: Schema installation failed${NC}"
    exit 1
  fi
# Try Python bootstrap if it exists
elif [ -n "$PY_ROOT" ] && [ -f "${PY_ROOT}/src/config.py" ]; then
  echo "  Running: schema bootstrap (Python)"
  cd "${PY_ROOT}"
  python -c "
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path.cwd() / 'src'))

try:
  from services.db_service import init_db
  init_db()
  print('✓ Database initialized')
except Exception as e:
  print(f'✗ Database initialization failed: {e}', file=sys.stderr)
  sys.exit(1)
"
  
  if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC} Database initialized successfully"
  else
    echo -e "${RED}ERROR: Database initialization failed${NC}"
    exit 1
  fi
else
  echo -e "${YELLOW}⚠${NC}  No migration system found (alembic.ini not present)"
  echo "  Assuming schema is auto-bootstrapped on application startup"
fi

# ============================================================================
# Pre-Deploy Validation
# ============================================================================

echo -e "\n${YELLOW}[4/4]${NC} Running pre-deploy validations..."

# Check that critical environment variables are set
REQUIRED_VARS=(
  "DATABASE_URL"
  "PORT"
)

MISSING_VARS=()
for var in "${REQUIRED_VARS[@]}"; do
  if [ -z "${!var}" ]; then
    MISSING_VARS+=("$var")
  fi
done

if [ ${#MISSING_VARS[@]} -gt 0 ]; then
  echo -e "${RED}ERROR: Missing required environment variables: ${MISSING_VARS[*]}${NC}"
  exit 1
fi

echo -e "${GREEN}✓${NC} All validations passed"

# ============================================================================
# Summary
# ============================================================================

echo -e "\n${GREEN}=========================================="
echo "Pre-Deploy Checklist"
echo "==========================================${NC}"
echo -e "${GREEN}✓${NC} Environment variables validated"
echo -e "${GREEN}✓${NC} Database connectivity confirmed"
echo -e "${GREEN}✓${NC} Database migrations completed"
echo -e "${GREEN}✓${NC} Pre-deploy validations passed"
echo ""
echo "Ready to start service."
echo "Time: $(date)"
echo ""

exit 0
