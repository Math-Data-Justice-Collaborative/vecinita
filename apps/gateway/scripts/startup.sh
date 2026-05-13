#!/bin/bash
#
# startup.sh - Auto-startup script for VECINA Docker Compose on Google VM
# 
# This script ensures docker-compose services start automatically on VM reboot.
# It includes health checks, logging, and graceful startup.
#
# Installation options:
# 1. Via systemd (recommended): sudo scripts/startup.sh --install-systemd
# 2. Via cron (@reboot): sudo scripts/startup.sh --install-cron
# 3. Manual Google Cloud startup script: Copy to VM metadata
#

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROJECT_DIR="$SCRIPT_DIR"
LOG_FILE="/var/log/vecinita-startup.log"
DOCKER_COMPOSE_FILE="$PROJECT_DIR/docker-compose.yml"
MAX_WAIT_TIME=60  # seconds to wait for docker-compose to be ready
STARTUP_DELAY=5   # seconds to wait before checking status

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging function
log() {
    local level=$1
    shift
    local message="$@"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] [$level] $message" | tee -a "$LOG_FILE"
}

# Ensure log file is writable
setup_logging() {
    if [[ ! -w "$(dirname "$LOG_FILE")" ]]; then
        LOG_FILE="/tmp/vecinita-startup.log"
        log "WARN" "Cannot write to $LOG_FILE, using $LOG_FILE instead"
    fi
}

# Wait for docker daemon to be ready
wait_for_docker() {
    log "INFO" "Waiting for Docker daemon..."
    local waited=0
    while ! docker info > /dev/null 2>&1; do
        if [ $waited -gt 30 ]; then
            log "ERROR" "Docker daemon not available after 30 seconds"
            return 1
        fi
        sleep 2
        waited=$((waited + 2))
    done
    log "INFO" "Docker daemon is ready"
    return 0
}

# Start docker-compose services
start_services() {
    log "INFO" "Starting docker-compose services from $PROJECT_DIR..."
    
    if [[ ! -f "$DOCKER_COMPOSE_FILE" ]]; then
        log "ERROR" "docker-compose.yml not found at $DOCKER_COMPOSE_FILE"
        return 1
    fi
    
    cd "$PROJECT_DIR"
    
    # Start in detached mode with build if needed
    if docker-compose up -d --build > /tmp/docker-compose.log 2>&1; then
        log "INFO" "docker-compose up -d completed successfully"
        return 0
    else
        log "ERROR" "docker-compose up -d failed"
        tail -20 /tmp/docker-compose.log >> "$LOG_FILE"
        return 1
    fi
}

# Check if services are healthy
check_health() {
    log "INFO" "Waiting for services to become healthy..."
    sleep "$STARTUP_DELAY"
    
    local waited=0
    while [ $waited -lt $MAX_WAIT_TIME ]; do
        # Check if containers are running
        local running_count=$(docker-compose ps --services --filter "status=running" 2>/dev/null | wc -l)
        local total_count=$(docker-compose ps --services 2>/dev/null | wc -l)
        
        if [ "$running_count" -eq "$total_count" ] && [ "$total_count" -gt 0 ]; then
            log "INFO" "✓ All services running ($running_count/$total_count)"
            return 0
        fi
        
        log "INFO" "Services starting... ($running_count/$total_count running)"
        sleep 5
        waited=$((waited + 5))
    done
    
    log "WARN" "Startup timeout reached, but containers may still be starting"
    docker-compose ps >> "$LOG_FILE"
    return 0  # Don't fail, services might still be starting
}

# Create systemd service file
install_systemd() {
    log "INFO" "Installing systemd service for auto-restart..."
    
    local service_file="/etc/systemd/system/vecinita-docker.service"
    
    cat > /tmp/vecinita-docker.service << EOF
[Unit]
Description=VECINA Docker Compose Service
After=docker.service
Requires=docker.service
Documentation=https://github.com/acadiagit/vecinita

[Service]
Type=oneshot
ExecStart=$SCRIPT_DIR/startup.sh --start
RemainAfterExit=yes
WorkingDirectory=$PROJECT_DIR
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

    if sudo cp /tmp/vecinita-docker.service "$service_file"; then
        sudo systemctl daemon-reload
        sudo systemctl enable vecinita-docker.service
        log "INFO" "✓ Systemd service installed and enabled"
        log "INFO" "Services will auto-start on reboot"
        log "INFO" "View logs: sudo journalctl -u vecinita-docker.service -f"
        return 0
    else
        log "ERROR" "Failed to install systemd service"
        return 1
    fi
}

# Install cron job
install_cron() {
    log "INFO" "Installing cron @reboot job..."
    
    local cron_entry="@reboot $SCRIPT_DIR/startup.sh --start"
    
    # Check if already installed
    if crontab -l 2>/dev/null | grep -q "vecinita"; then
        log "WARN" "Cron entry already exists, skipping installation"
        return 0
    fi
    
    # Add to crontab
    (crontab -l 2>/dev/null; echo "$cron_entry") | crontab -
    
    log "INFO" "✓ Cron @reboot job installed"
    log "INFO" "Services will auto-start on reboot"
    return 0
}

# Create Google Cloud startup script
install_gcloud() {
    log "INFO" "Creating Google Cloud startup script snippet..."
    
    local gcloud_script="/tmp/vecinita-gcloud-startup.sh"
    
    cat > "$gcloud_script" << 'EOF'
#!/bin/bash
# Add this to Google Cloud VM startup script metadata:
# Compute Engine > VM instances > [instance] > Edit > Custom metadata
# Key: startup-script, Value: [paste contents of this file]

cd /root/vecinita  # Adjust to your project path
docker-compose up -d
EOF

    log "INFO" "Google Cloud startup script template created at $gcloud_script"
    log "INFO" "Option 1: Use via metadata:"
    log "INFO" "  gcloud compute instances add-metadata INSTANCE_NAME \\"
    log "INFO" "    --metadata startup-script-url=gs://your-bucket/vecinita-startup.sh"
    log "INFO" "Option 2: Paste script into Console > VM > Edit > Custom metadata"
    return 0
}

# Main function
main() {
    setup_logging
    
    case "${1:-}" in
        --start)
            log "INFO" "=== VECINITA STARTUP SEQUENCE ==="
            wait_for_docker || exit 1
            start_services || exit 1
            check_health
            log "INFO" "=== STARTUP COMPLETE ==="
            ;;
        --install-systemd)
            install_systemd
            ;;
        --install-cron)
            install_cron
            ;;
        --install-gcloud)
            install_gcloud
            ;;
        *)
            cat << 'USAGE'
VECINITA Docker Compose Auto-Startup Script

Usage: ./scripts/startup.sh [OPTION]

OPTIONS:
  --start              Start docker-compose services (default action)
  --install-systemd    Install as systemd service (recommended, requires sudo)
  --install-cron       Install as cron @reboot job (requires sudo)
  --install-gcloud     Show Google Cloud startup script setup
  --help               Show this help message

INSTALLATION METHODS:

1. SYSTEMD (Recommended for Google VM - most robust):
   sudo ./scripts/startup.sh --install-systemd
   View logs: sudo journalctl -u vecinita-docker.service -f

2. CRON (Simple alternative):
   sudo ./scripts/startup.sh --install-cron
   View logs: /tmp/vecinita-startup.log

3. GOOGLE CLOUD METADATA (Built into VM):
   gcloud compute instances add-metadata INSTANCE_NAME \
     --metadata startup-script-url=gs://your-bucket/startup.sh

4. DOCKER RESTART POLICY (Already configured in docker-compose.yml):
   Services with restart: always will auto-restart if they crash

LOGS:
   Systemd:  sudo journalctl -u vecinita-docker.service -f
   File:     tail -f /var/log/vecinita-startup.log or /tmp/vecinita-startup.log
   Docker:   docker-compose logs -f

TESTING:
   Test startup script: ./scripts/startup.sh --start
   Test systemd service: sudo systemctl start vecinita-docker.service
   Verify running: docker-compose ps

USAGE
            exit 0
            ;;
    esac
}

main "$@"
