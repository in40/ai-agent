#!/bin/bash

# Script to stop all AI Agent services

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Stopping all AI Agent services...${NC}"

# Read PIDs from file if it exists
if [ -f service_pids.txt ]; then
    source service_pids.txt
    
    # Kill all background processes
    for pid_var in AUTH_PID AGENT_PID RAG_PID GATEWAY_PID LANGGRAPH_PID STREAMLIT_PID REACT_PID; do
        pid_val=${!pid_var}
        if [ ! -z "$pid_val" ] && kill -0 $pid_val 2>/dev/null; then
            echo -e "${YELLOW}Stopping $pid_var (PID: $pid_val)...${NC}"
            kill $pid_val 2>/dev/null || true
        fi
    done
    
    # Remove PID file
    rm -f service_pids.txt
    echo -e "${GREEN}Service PIDs file removed.${NC}"
else
    echo -e "${YELLOW}No service PIDs file found. Attempting to stop services by port...${NC}"
    
    # Kill processes by port if PID file doesn't exist
    for port in 5000 5001 5002 5003 8000 8501 3000; do
        pid=$(lsof -t -i:$port 2>/dev/null)
        if [ ! -z "$pid" ]; then
            echo -e "${YELLOW}Stopping process on port $port (PID: $pid)...${NC}"
            kill $pid 2>/dev/null || true
        fi
    done
fi

# Stop Redis if running
if command -v redis-cli >/dev/null 2>&1; then
    if nc -z localhost 6379 2>/dev/null; then
        echo -e "${YELLOW}Stopping Redis...${NC}"
        redis-cli shutdown 2>/dev/null || true
    fi
fi

echo -e "${GREEN}All services stopped.${NC}"