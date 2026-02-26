#!/bin/bash
# ==============================================================================
# SCRIPT: run_beta.sh
# DESCRIPTION: Starts the Vecinita Beta container.
#              Loads PROJECT_ROOT from .env as the Single Source of Truth.
# AUTHOR: Vecinita Dev Team
# DATE: 2026-01-25
# ==============================================================================

echo "🚀 Bootstrapping Vecinita..."

# 1. Locate the Project Root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(dirname "$SCRIPT_DIR")"
ENV_FILE="$BASE_DIR/.env"

# 2. Load the Single Source of Truth (.env)
if [ -f "$ENV_FILE" ]; then
    echo "📄 Loading environment from: $ENV_FILE"
    set -a
    source "$ENV_FILE"
    set +a
else
    echo "❌ Error: .env file not found at $ENV_FILE"
    exit 1
fi

# 3. Validate PROJECT_ROOT
if [ -z "$PROJECT_ROOT" ]; then
    echo "❌ Error: PROJECT_ROOT variable is missing in .env!"
    echo "👉 Please add: PROJECT_ROOT=/mnt/data_prod/vecinita"
    exit 1
fi

# 4. Configure Paths
LOG_DIR="$PROJECT_ROOT/logs"

echo "📂 Project Root: $PROJECT_ROOT"
echo "📝 Log Target:   $LOG_DIR"

# 5. Prepare Directories
mkdir -p "$LOG_DIR"
chmod 777 "$LOG_DIR"

# 6. Run Docker
docker run --rm -p 8000:8000 \
  --env-file "$ENV_FILE" \
  -v "$LOG_DIR":/app/logs \
  --name vecinita_beta \
  vecinita:beta

# END OF FILE
