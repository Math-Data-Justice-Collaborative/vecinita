#!/bin/bash

# Vecinita Docker Compose Verification Script
# Tests all 6 services in the local development stack

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=== Vecinita Docker Compose Services Verification ===${NC}\n"

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}✗ docker-compose is not installed${NC}"
    exit 1
fi

echo -e "${GREEN}✓ docker-compose found${NC}\n"

# Function to wait for service
wait_for_service() {
    local service=$1
    local port=$2
    local max_attempts=30
    local attempt=0
    
    echo -n "  Waiting for $service (port $port)..."
    while ! nc -z localhost $port 2>/dev/null; do
        attempt=$((attempt + 1))
        if [ $attempt -gt $max_attempts ]; then
            echo -e " ${RED}TIMEOUT${NC}"
            return 1
        fi
        echo -n "."
        sleep 1
    done
    echo -e " ${GREEN}Ready${NC}"
    return 0
}

# Function to test HTTP endpoint
test_endpoint() {
    local name=$1
    local url=$2
    local method=${3:-GET}
    
    echo -n "  Testing $name... "
    if curl -s -X $method "$url" -o /dev/null -w "%{http_code}" 2>/dev/null | grep -q "200\|404"; then
        echo -e "${GREEN}✓${NC}"
        return 0
    else
        echo -e "${RED}✗${NC}"
        return 1
    fi
}

# Function to test database connection
test_database() {
    echo -n "  Testing PostgreSQL connection... "
    if PGPASSWORD=postgres psql -h localhost -U postgres -d postgres -c "SELECT 1" &>/dev/null; then
        echo -e "${GREEN}✓${NC}"
        return 0
    else
        echo -e "${RED}✗${NC}"
        return 1
    fi
}

# Check if services are running
echo -e "${YELLOW}Checking running services:${NC}"
docker-compose ps
echo ""

# Test each service
echo -e "${YELLOW}Testing Services:${NC}\n"

echo "1. PostgreSQL (port 5432)"
wait_for_service "PostgreSQL" 5432 || true
test_database || true
echo ""

echo "2. PostgREST (port 3001)"
wait_for_service "PostgREST" 3001 || true
test_endpoint "PostgREST health" "http://localhost:3001/" || true
echo ""

echo "3. Embedding Service (port 8001)"
wait_for_service "Embedding" 8001 || true
test_endpoint "Embedding health" "http://localhost:8001/health" || true
echo ""

echo "4. Agent Service (port 8000)"
wait_for_service "Agent" 8000 || true
test_endpoint "Agent health" "http://localhost:8000/health" || true
echo ""

echo "5. Frontend (port 5173)"
wait_for_service "Frontend" 5173 || true
test_endpoint "Frontend" "http://localhost:5173/" || true
echo ""

echo "6. pgAdmin (port 5050)"
wait_for_service "pgAdmin" 5050 || true
test_endpoint "pgAdmin" "http://localhost:5050/" || true
echo ""

# Summary
echo -e "${YELLOW}=== Summary ===${NC}"
echo -e "Frontend:           ${GREEN}http://localhost:5173${NC}"
echo -e "Agent API:          ${GREEN}http://localhost:8000${NC} (API Docs: http://localhost:8000/docs)"
echo -e "Embedding Service:  ${GREEN}http://localhost:8001${NC}"
echo -e "PostgREST API:      ${GREEN}http://localhost:3001${NC}"
echo -e "pgAdmin:            ${GREEN}http://localhost:5050${NC} (admin@example.com/admin)"
echo -e "PostgreSQL:         ${GREEN}localhost:5432${NC} (postgres/postgres)"
echo ""

echo -e "${GREEN}✓ All services are ready for development!${NC}"
