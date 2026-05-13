#!/bin/bash
# ==============================================================================
# SCRIPT: daily_cleanup.sh
# DESCRIPTION: Removes unused "dangling" Docker images and stopped containers
#              to prevent disk space exhaustion during development.
# AUTHOR: Vecinita Dev Team
# DATE: 2026-01-25
# ==============================================================================

# 1. Define Log Location (Same folder as your app logs)
LOG_FILE="/mnt/data_prod/vecinita/logs/docker_cleanup.log"

echo "🧹 [$(date)] Starting Daily Docker Cleanup..." >> "$LOG_FILE"

# 2. Prune Dangling Images (The old "none:none" layers from rebuilds)
#    -f : Force (no confirmation prompt)
#    --filter "dangling=true" : Only delete images that have no name
docker image prune -f --filter "dangling=true" >> "$LOG_FILE" 2>&1

# 3. Optional: Prune Stopped Containers (Keeps the list clean)
docker container prune -f >> "$LOG_FILE" 2>&1

echo "✨ [$(date)] Cleanup Complete." >> "$LOG_FILE"
echo "---------------------------------------------------" >> "$LOG_FILE"

# END OF FILE
