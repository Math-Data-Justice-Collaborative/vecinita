#!/bin/bash
# Start All Vecinita Services Locally
# This script starts all services in parallel using tmux sessions
# Requirements: tmux, uv

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  Vecinita - Starting All Services${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"

# Check if tmux is installed
if ! command -v tmux &> /dev/null; then
    echo -e "${YELLOW}tmux not found. Installing...${NC}"
    sudo apt-get update && sudo apt-get install -y tmux
fi

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo -e "${YELLOW}uv not found. Please install: curl -LsSf https://astral.sh/uv/install.sh | sh${NC}"
    exit 1
fi

# Kill existing tmux session if it exists
tmux kill-session -t vecinita 2>/dev/null || true

# Create new tmux session
echo -e "${GREEN}Creating tmux session 'vecinita'...${NC}"
tmux new-session -d -s vecinita -n services

# Split window into panes
tmux split-window -h -t vecinita:services
tmux split-window -v -t vecinita:services.0

# Set environment variables for all panes
tmux send-keys -t vecinita:services.0 "export AGENT_SERVICE_URL=http://localhost:8000" C-m
tmux send-keys -t vecinita:services.1 "export EMBEDDING_SERVICE_URL=http://localhost:8001" C-m
tmux send-keys -t vecinita:services.2 "export DEMO_MODE=false" C-m

# Wait a moment for environment variables to be set
sleep 1

# Start Agent Service (Pane 0)
echo -e "${GREEN}Starting Agent Service on port 8000...${NC}"
tmux send-keys -t vecinita:services.0 "cd /root/GitHub/VECINA/vecinita/backend" C-m
tmux send-keys -t vecinita:services.0 "echo -e '${GREEN}[Agent Service - Port 8000]${NC}'" C-m
tmux send-keys -t vecinita:services.0 "uv run uvicorn src.agent.main:app --host 0.0.0.0 --port 8000" C-m

# Start Embedding Service (Pane 1)
echo -e "${GREEN}Starting Embedding Service on port 8001...${NC}"
tmux send-keys -t vecinita:services.1 "cd /root/GitHub/VECINA/vecinita/backend" C-m
tmux send-keys -t vecinita:services.1 "echo -e '${GREEN}[Embedding Service - Port 8001]${NC}'" C-m
tmux send-keys -t vecinita:services.1 "uv run uvicorn src.embedding_service.main:app --host 0.0.0.0 --port 8001" C-m

# Wait for services to start
echo -e "${YELLOW}Waiting for services to start (5 seconds)...${NC}"
sleep 5

# Start Gateway (Pane 2)
echo -e "${GREEN}Starting API Gateway on port 8004...${NC}"
tmux send-keys -t vecinita:services.2 "cd /root/GitHub/VECINA/vecinita/backend" C-m
tmux send-keys -t vecinita:services.2 "echo -e '${GREEN}[API Gateway - Port 8004]${NC}'" C-m
tmux send-keys -t vecinita:services.2 "export AGENT_SERVICE_URL=http://localhost:8000 && export DEMO_MODE=false && uv run uvicorn src.api.main:app --host 0.0.0.0 --port 8004 --reload --reload-dir src --reload-exclude '.mypy_cache/*' --reload-exclude '.pytest_cache/*' --reload-exclude '.ruff_cache/*' --reload-exclude '.venv/*' --reload-exclude 'logs/*' --reload-exclude 'build/*' --reload-exclude 'coverage*' --reload-exclude '*.pyc'" C-m

echo ""
echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✓ All services started!${NC}"
echo ""
echo -e "${YELLOW}Services:${NC}"
echo -e "  ${GREEN}Agent Service:${NC}     http://localhost:8000/health"
echo -e "  ${GREEN}Embedding Service:${NC} http://localhost:8001/health"
echo -e "  ${GREEN}API Gateway:${NC}       http://localhost:8004/"
echo -e "  ${GREEN}Swagger Docs:${NC}      http://localhost:8004/api/v1/docs"
echo ""
echo -e "${YELLOW}Commands:${NC}"
echo -e "  ${GREEN}Attach to session:${NC}  tmux attach -t vecinita"
echo -e "  ${GREEN}Switch panes:${NC}       Ctrl+b then arrow keys"
echo -e "  ${GREEN}Detach session:${NC}     Ctrl+b then d"
echo -e "  ${GREEN}Kill all services:${NC}  tmux kill-session -t vecinita"
echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"

# Attach to the session
tmux attach -t vecinita
