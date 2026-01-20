#!/bin/bash

# Startup script for the AI Agent microservices architecture

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting AI Agent System - Microservices Architecture...${NC}"

# Get the project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

# Activate the virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source "$PROJECT_ROOT/ai_agent_env/bin/activate"

# Start Redis if not already running
if ! nc -z localhost 6379; then
    echo -e "${YELLOW}Starting Redis...${NC}"
    redis-server --daemonize yes
    sleep 2
else
    echo -e "${GREEN}Redis is already running${NC}"
fi

# Start the auth service in the background
echo -e "${YELLOW}Starting authentication service...${NC}"
cd "$PROJECT_ROOT"
export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"
nohup python -m backend.services.auth.app > auth_service.log 2>&1 &
AUTH_PID=$!
echo -e "${GREEN}Authentication service started with PID $AUTH_PID${NC}"

# Wait a moment for the auth service to start
sleep 3

# Start the agent service in the background
echo -e "${YELLOW}Starting agent service...${NC}"
nohup python -m backend.services.agent.app > agent_service.log 2>&1 &
AGENT_PID=$!
echo -e "${GREEN}Agent service started with PID $AGENT_PID${NC}"

# Wait a moment for the agent service to start
sleep 3

# Start the RAG service in the background
echo -e "${YELLOW}Starting RAG service...${NC}"
nohup python -m backend.services.rag.app > rag_service.log 2>&1 &
RAG_PID=$!
echo -e "${GREEN}RAG service started with PID $RAG_PID${NC}"

# Wait a moment for the RAG service to start
sleep 3

# Start the gateway in the background
echo -e "${YELLOW}Starting API gateway...${NC}"
nohup python -m backend.services.gateway.app > gateway.log 2>&1 &
GATEWAY_PID=$!
echo -e "${GREEN}Gateway started with PID $GATEWAY_PID${NC}"

# Wait a bit more for services to start
sleep 5

echo -e "${GREEN}"
echo "=========================================================="
echo "AI AGENT MICROSERVICES ARE NOW RUNNING"
echo "=========================================================="
echo "API Gateway:         http://localhost:5000"
echo "Authentication:      http://localhost:5001"
echo "Agent Service:       http://localhost:5002"
echo "RAG Service:         http://localhost:5003"
echo "Redis:               http://localhost:6379"
echo "=========================================================="
echo -e "${NC}"

# Keep the script running
echo -e "${YELLOW}Press Ctrl+C to stop the system${NC}"

# Function to handle shutdown
cleanup() {
    echo -e "\n${YELLOW}Stopping AI Agent Microservices...${NC}"
    
    # Kill all background processes
    for pid in $AUTH_PID $AGENT_PID $RAG_PID $GATEWAY_PID; do
        if [ ! -z "$pid" ]; then
            kill $pid 2>/dev/null || true
        fi
    done
    
    # Stop Redis if we started it
    if [ ! -z "$REDIS_STARTED" ]; then
        redis-cli shutdown
    fi
    
    echo -e "${GREEN}Microservices stopped.${NC}"
    exit 0
}

# Trap SIGINT and SIGTERM
trap cleanup INT TERM

# Wait indefinitely
while true; do
    sleep 1
done