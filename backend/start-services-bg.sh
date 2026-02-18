#!/bin/bash
# Simple Background Process Startup for Vecinita Services
# This script starts services as background processes with logs
# Simpler alternative to tmux-based startup

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

BACKEND_DIR="/root/GitHub/VECINA/vecinita/backend"
LOG_DIR="$BACKEND_DIR/logs"
PID_DIR="$BACKEND_DIR/.pids"

# Create log and PID directories
mkdir -p "$LOG_DIR" "$PID_DIR"

echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  Vecinita - Starting Services (Background Mode)${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"

# Function to stop all services
stop_services() {
    echo -e "\n${YELLOW}Stopping all services...${NC}"
    
    if [ -f "$PID_DIR/agent.pid" ]; then
        kill $(cat "$PID_DIR/agent.pid") 2>/dev/null && echo -e "${GREEN}✓ Agent service stopped${NC}"
    fi
    
    if [ -f "$PID_DIR/embedding.pid" ]; then
        kill $(cat "$PID_DIR/embedding.pid") 2>/dev/null && echo -e "${GREEN}✓ Embedding service stopped${NC}"
    fi
    
    if [ -f "$PID_DIR/gateway.pid" ]; then
        kill $(cat "$PID_DIR/gateway.pid") 2>/dev/null && echo -e "${GREEN}✓ Gateway stopped${NC}"
    fi
    
    rm -f "$PID_DIR"/*.pid
    echo -e "${GREEN}All services stopped${NC}"
}

# Handle Ctrl+C
trap stop_services EXIT INT TERM

# Check if services are already running
if [ -f "$PID_DIR/gateway.pid" ] && kill -0 $(cat "$PID_DIR/gateway.pid") 2>/dev/null; then
    echo -e "${RED}Services already running. Stop them first with:${NC}"
    echo -e "  pkill -f 'uvicorn src.api.main'"
    echo -e "  pkill -f 'uvicorn src.services'"
    exit 1
fi

# Start Agent Service
echo -e "${GREEN}Starting Agent Service on port 8000...${NC}"
cd "$BACKEND_DIR"
nohup uv run uvicorn src.services.agent.server:app --host 0.0.0.0 --port 8000 \
    > "$LOG_DIR/agent.log" 2>&1 &
echo $! > "$PID_DIR/agent.pid"
sleep 2

# Check if agent started successfully
if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "  ${GREEN}✓ Agent service started (PID: $(cat $PID_DIR/agent.pid))${NC}"
else
    echo -e "  ${RED}✗ Agent service failed to start. Check logs:${NC}"
    echo -e "    tail -f $LOG_DIR/agent.log"
    exit 1
fi

# Start Embedding Service
echo -e "${GREEN}Starting Embedding Service on port 8001...${NC}"
nohup uv run uvicorn src.services.embedding.server:app --host 0.0.0.0 --port 8001 \
    > "$LOG_DIR/embedding.log" 2>&1 &
echo $! > "$PID_DIR/embedding.pid"
sleep 2

# Check if embedding started successfully
if curl -sf http://localhost:8001/health > /dev/null 2>&1; then
    echo -e "  ${GREEN}✓ Embedding service started (PID: $(cat $PID_DIR/embedding.pid))${NC}"
else
    echo -e "  ${YELLOW}⚠ Embedding service may still be loading...${NC}"
fi

# Start API Gateway with explicit environment variables
echo -e "${GREEN}Starting API Gateway on port 8004...${NC}"
export AGENT_SERVICE_URL=http://localhost:8000
export EMBEDDING_SERVICE_URL=http://localhost:8001
export DEMO_MODE=false

nohup uv run uvicorn src.api.main:app --host 0.0.0.0 --port 8004 --reload \
    > "$LOG_DIR/gateway.log" 2>&1 &
echo $! > "$PID_DIR/gateway.pid"
sleep 3

# Check if gateway started successfully
if curl -sf http://localhost:8004/health > /dev/null 2>&1; then
    echo -e "  ${GREEN}✓ Gateway started (PID: $(cat $PID_DIR/gateway.pid))${NC}"
else
    echo -e "  ${RED}✗ Gateway failed to start. Check logs:${NC}"
    echo -e "    tail -f $LOG_DIR/gateway.log"
    exit 1
fi

echo ""
echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✓ All services started successfully!${NC}"
echo ""
echo -e "${YELLOW}Services:${NC}"
echo -e "  ${GREEN}Agent Service:${NC}     http://localhost:8000/health"
echo -e "  ${GREEN}Embedding Service:${NC} http://localhost:8001/health"
echo -e "  ${GREEN}API Gateway:${NC}       http://localhost:8004/"
echo -e "  ${GREEN}Swagger Docs:${NC}      http://localhost:8004/api/v1/docs"
echo ""
echo -e "${YELLOW}Logs:${NC}"
echo -e "  ${GREEN}Agent:${NC}     tail -f $LOG_DIR/agent.log"
echo -e "  ${GREEN}Embedding:${NC} tail -f $LOG_DIR/embedding.log"
echo -e "  ${GREEN}Gateway:${NC}   tail -f $LOG_DIR/gateway.log"
echo ""
echo -e "${YELLOW}Process IDs:${NC}"
echo -e "  ${GREEN}Agent:${NC}     $(cat $PID_DIR/agent.pid)"
echo -e "  ${GREEN}Embedding:${NC} $(cat $PID_DIR/embedding.pid)"
echo -e "  ${GREEN}Gateway:${NC}   $(cat $PID_DIR/gateway.pid)"
echo ""
echo -e "${YELLOW}Commands:${NC}"
echo -e "  ${GREEN}View all logs:${NC}     tail -f $LOG_DIR/*.log"
echo -e "  ${GREEN}Stop all services:${NC} pkill -f 'uvicorn src'"
echo -e "  ${GREEN}Or run:${NC}            kill \$(cat $PID_DIR/*.pid)"
echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop all services, or run this script again with 'stop' to stop manually.${NC}"

# Keep script running to maintain trap
if [ "$1" != "daemon" ]; then
    echo -e "${YELLOW}Running in foreground mode. Press Ctrl+C to stop all services.${NC}"
    wait
fi
