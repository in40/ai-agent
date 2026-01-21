#!/bin/bash

# Script to check the status of AI Agent services

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Checking status of AI Agent services...${NC}"
echo "=================================================="

# Check each service by port
ports=(
    "5000:API Gateway"
    "5001:Authentication Service"
    "5002:Agent Service"
    "5003:RAG Service"
    "8000:LangGraph Studio"
    "8501:Streamlit App"
    "3000:React Editor"
)

all_running=true

for entry in "${ports[@]}"; do
    port=${entry%%:*}
    name=${entry#*:}
    
    if nc -z localhost $port 2>/dev/null; then
        pid=$(lsof -t -i:$port 2>/dev/null)
        echo -e "  ${GREEN}✓${NC} $name - Port $port (PID: $pid)"
    else
        echo -e "  ${RED}✗${NC} $name - Port $port (Not running)"
        all_running=false
    fi
done

echo "=================================================="

# Check Redis
if nc -z localhost 6379 2>/dev/null; then
    echo -e "  ${GREEN}✓${NC} Redis - Port 6379"
else
    echo -e "  ${YELLOW}~${NC} Redis - Port 6379 (Not running)"
fi

echo ""
if [ "$all_running" = true ]; then
    echo -e "${GREEN}All services are running.${NC}"
else
    echo -e "${YELLOW}Some services are not running.${NC}"
fi

echo ""
echo -e "${GREEN}Service URLs:${NC}"
echo "  Web Client:          https://192.168.51.138 (via gateway)"
echo "  API Gateway:         http://192.168.51.138:5000"
echo "  Authentication:      http://192.168.51.138:5001"
echo "  Agent Service:       http://192.168.51.138:5002"
echo "  RAG Service:         http://192.168.51.138:5003"
echo "  LangGraph Studio:    http://192.168.51.138:8000"
echo "  Streamlit App:       http://192.168.51.138:8501"
echo "  React Editor:        http://192.168.51.138:3000"