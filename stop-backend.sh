#!/bin/bash

# Script to cleanly stop the backend server

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}🛑 Stopping backend server...${NC}"

# Kill any processes on port 8000
PIDS=$(lsof -ti:8000 2>/dev/null)
if [ ! -z "$PIDS" ]; then
    echo -e "${YELLOW}📦 Found processes: $PIDS${NC}"
    echo -e "${YELLOW}🔪 Killing processes...${NC}"
    kill -9 $PIDS 2>/dev/null
    sleep 1
    echo -e "${GREEN}✅ Backend stopped successfully${NC}"
else
    echo -e "${YELLOW}⚠️  No backend processes found${NC}"
fi

# Optionally show what's still running
echo ""
echo -e "${YELLOW}📊 Service Status:${NC}"
echo -e "Redis:      $(docker ps | grep redis > /dev/null 2>&1 && echo 'running (Docker)' || echo 'stopped')"
echo -e "PostgreSQL: $(docker ps | grep postgres > /dev/null 2>&1 && echo 'running (Docker)' || echo 'stopped')"
echo -e "Qdrant:     $(curl -s http://localhost:6333/health > /dev/null && echo 'running' || echo 'stopped')"
echo -e "Ollama:     $(curl -s http://localhost:11434/api/tags > /dev/null && echo 'running' || echo 'stopped')"
