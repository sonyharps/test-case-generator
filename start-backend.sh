#!/bin/bash

# Script to cleanly start the backend server

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}🔍 Checking for existing processes on port 8000...${NC}"

# Method 1: Kill by port
PIDS=$(lsof -ti:8000 2>/dev/null)
if [ ! -z "$PIDS" ]; then
    echo -e "${YELLOW}📦 Found processes on port: $PIDS${NC}"
    kill -9 $PIDS 2>/dev/null
    sleep 1
fi

# Method 2: Kill by uvicorn process name (catches hung processes)
UVICORN_PIDS=$(pgrep -f "uvicorn app.main:app" 2>/dev/null)
if [ ! -z "$UVICORN_PIDS" ]; then
    echo -e "${YELLOW}🔪 Killing uvicorn processes: $UVICORN_PIDS${NC}"
    kill -9 $UVICORN_PIDS 2>/dev/null
    sleep 1
fi

# Verify port is clear
if lsof -ti:8000 >/dev/null 2>&1; then
    echo -e "${RED}❌ ERROR: Port 8000 still in use!${NC}"
    echo -e "${YELLOW}Run manually: lsof -ti:8000 | xargs kill -9${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Port 8000 is clear${NC}"

# Check if Redis is running (Docker)
echo -e "${YELLOW}🔍 Checking Redis connection...${NC}"
if docker ps | grep redis > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Redis is running (Docker)${NC}"
elif nc -z localhost 6379 > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Redis is running (port 6379 open)${NC}"
else
    echo -e "${RED}❌ Redis is not running!${NC}"
    echo -e "${YELLOW}Please start Redis with: docker start qa-orchestrator-redis${NC}"
    exit 1
fi

# Check if Qdrant is running
echo -e "${YELLOW}🔍 Checking Qdrant connection...${NC}"
if ! curl -s http://localhost:6333/health > /dev/null; then
    echo -e "${RED}❌ Qdrant is not running!${NC}"
    echo -e "${YELLOW}Please start Qdrant with: docker start qdrant${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Qdrant is running${NC}"

# Check if PostgreSQL is running (Docker or native)
echo -e "${YELLOW}🔍 Checking PostgreSQL connection...${NC}"
if docker ps | grep postgres > /dev/null 2>&1; then
    echo -e "${GREEN}✅ PostgreSQL is running (Docker)${NC}"
elif pg_isready -h localhost -p 5432 > /dev/null 2>&1; then
    echo -e "${GREEN}✅ PostgreSQL is running${NC}"
elif nc -z localhost 5432 > /dev/null 2>&1; then
    echo -e "${GREEN}✅ PostgreSQL is running (port 5432 open)${NC}"
else
    echo -e "${RED}❌ PostgreSQL is not running!${NC}"
    echo -e "${YELLOW}Please start PostgreSQL with: docker start qa-orchestrator-db${NC}"
    exit 1
fi

# Check if Ollama is running
echo -e "${YELLOW}🔍 Checking Ollama...${NC}"
if ! curl -s http://localhost:11434/api/tags > /dev/null; then
    echo -e "${YELLOW}⚠️  Ollama might not be running${NC}"
    echo -e "${YELLOW}Please start Ollama if needed${NC}"
else
    echo -e "${GREEN}✅ Ollama is running${NC}"
fi

echo ""
echo -e "${GREEN}🚀 Starting backend server...${NC}"
echo ""

# Change to script directory
cd "$(dirname "$0")"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo -e "${YELLOW}🐍 Activating virtual environment...${NC}"
    source venv/bin/activate
elif [ -d ".venv" ]; then
    echo -e "${YELLOW}🐍 Activating virtual environment...${NC}"
    source .venv/bin/activate
fi

# Start the backend
uvicorn app.main:app --reload
