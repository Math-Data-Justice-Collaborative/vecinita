#!/bin/bash

# Vecinita One-Command Setup & Start
# Sets up local development environment and starts all 6 services

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "╔═══════════════════════════════════════════════════════╗"
echo "║     Vecinita Full Stack - Local Development Setup     ║"
echo "╚═══════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Check prerequisites
echo -e "\n${YELLOW}1. Checking prerequisites...${NC}"

if ! command -v docker &> /dev/null; then
    echo -e "${RED}✗ Docker is not installed${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Docker found${NC}"

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}✗ docker-compose is not installed${NC}"
    exit 1
fi
echo -e "${GREEN}✓ docker-compose found${NC}"

# Setup environment
echo -e "\n${YELLOW}2. Setting up environment...${NC}"

if [ ! -f ".env" ]; then
    if [ -f ".env.local" ]; then
        cp .env.local .env
        echo -e "${GREEN}✓ Created .env from .env.local${NC}"
    else
        echo -e "${RED}✗ .env.local not found${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✓ .env already exists${NC}"
fi

# Validate docker-compose
echo -e "\n${YELLOW}3. Validating docker-compose.yml...${NC}"

if docker-compose config --quiet 2>&1 | grep -q "error\|Error"; then
    echo -e "${RED}✗ docker-compose.yml has errors${NC}"
    docker-compose config
    exit 1
fi
echo -e "${GREEN}✓ docker-compose.yml is valid${NC}"

# Check git submodules
echo -e "\n${YELLOW}4. Checking git submodules...${NC}"

if [ -d ".git" ]; then
    git submodule update --init --recursive --quiet 2>/dev/null || true
    # vecinita-scraper: pull.ff=true aborts with "Not possible to fast-forward" when local/main
    # and origin/main have diverged; rebase pulls need pull.ff=false.
    if [ -f "modal-apps/scraper/.git" ]; then
        git -C modal-apps/scraper config pull.rebase true
        git -C modal-apps/scraper config pull.ff false
        git -C modal-apps/scraper config merge.ff false
        git -C modal-apps/scraper config branch.main.rebase true
    fi
    echo -e "${GREEN}✓ Git submodules initialized${NC}"
fi

# Build/Start services
echo -e "\n${YELLOW}5. Starting services (this may take 2-3 minutes on first run)...${NC}"
echo -e "   Services being started:"
echo -e "   • PostgreSQL (5432)"
echo -e "   • pgAdmin UI (5050)"
echo -e "   • Embedding Service (8001)"
echo -e "   • Agent Service (8000)"
echo -e "   • Frontend UI (5173)"
echo ""

docker-compose up -d --build

# Wait for services
echo -e "\n${YELLOW}6. Waiting for services to be healthy...${NC}"

services=("postgres:5432" "embedding-service:8001" "vecinita-agent:8000" "vecinita-frontend:5173")
max_attempts=30
attempt=0

for service in "${services[@]}"; do
    IFS=':' read -r name port <<< "$service"
    echo -n "  Waiting for $name (port $port)... "
    
    attempt=0
    while ! docker-compose ps $name 2>/dev/null | grep -q "Up"; do
        attempt=$((attempt + 1))
        if [ $attempt -gt $max_attempts ]; then
            echo -e "${YELLOW}(still starting)${NC}"
            break
        fi
        sleep 2
    done
    echo -e "${GREEN}✓${NC}"
done

echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✓ All services started!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo ""

# Display service URLs
echo -e "${BLUE}Available Services:${NC}"
echo ""
echo -e "  ${YELLOW}Frontend (React)${NC}"
echo -e "  → http://localhost:5173"
echo ""
echo -e "  ${YELLOW}Agent API (FastAPI + LangGraph)${NC}"
echo -e "  → http://localhost:8000"
echo -e "  → API Docs: http://localhost:8000/docs"
echo ""
echo -e "  ${YELLOW}Embedding Service${NC}"
echo -e "  → http://localhost:8001/health"
echo ""
echo -e "  ${YELLOW}pgAdmin (Database UI)${NC}"
echo -e "  → http://localhost:5050"
echo -e "  → Login: admin@example.com / admin"
echo ""
echo -e "  ${YELLOW}PostgreSQL (Direct Connection)${NC}"
echo -e "  → localhost:5432"
echo -e "  → User: postgres / Password: postgres"
echo ""

# Show useful commands
echo -e "${BLUE}Useful Commands:${NC}"
echo ""
echo -e "  ${YELLOW}View running services:${NC}"
echo -e "  docker-compose ps"
echo ""
echo -e "  ${YELLOW}View service logs:${NC}"
echo -e "  docker-compose logs -f <service_name>"
echo ""
echo -e "  ${YELLOW}Stop all services:${NC}"
echo -e "  docker-compose down"
echo ""
echo -e "  ${YELLOW}Verify all services are healthy:${NC}"
echo -e "  ./backend/scripts_local/verify_services.sh"
echo ""
echo -e "  ${YELLOW}Deploy to Modal:${NC}"
echo -e "  ./backend/scripts/deploy_modal.sh --embedding"
echo ""

# Open frontend if possible
if command -v xdg-open &> /dev/null; then
    echo -e "\n${BLUE}Opening frontend in browser...${NC}"
    xdg-open http://localhost:5173 2>/dev/null || true
elif command -v open &> /dev/null; then
    echo -e "\n${BLUE}Opening frontend in browser...${NC}"
    open http://localhost:5173 2>/dev/null || true
fi

echo -e "\n${GREEN}✓ Setup complete! Happy coding! 🎉${NC}\n"
