#!/bin/bash
# Script to stop all LangGraph Editor GUI services

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Stopping all LangGraph Editor GUI services...${NC}"

# Function to stop a service by port
stop_service_by_port() {
    local port=$1
    local name=$2
    
    # Find the process ID listening on the specified port
    local pid=$(lsof -Pi :$port -sTCP:LISTEN -t 2>/dev/null)
    
    if [ -n "$pid" ]; then
        echo -e "${YELLOW}Stopping $name (PID: $pid) on port $port...${NC}"
        kill -TERM $pid 2>/dev/null
        
        # Wait a moment to allow graceful shutdown
        sleep 2
        
        # Check if process is still running and force kill if necessary
        if kill -0 $pid 2>/dev/null; then
            echo -e "${YELLOW}Force stopping $name (PID: $pid)...${NC}"
            kill -KILL $pid 2>/dev/null
        fi
        
        echo -e "${GREEN}$name on port $port stopped.${NC}"
    else
        echo -e "${GREEN}$name on port $port was not running.${NC}"
    fi
}

# Stop services in reverse order
stop_service_by_port "5001" "Workflow API"
stop_service_by_port "8000" "LangGraph Studio"
stop_service_by_port "8501" "Streamlit App"
stop_service_by_port "3000" "React Editor"

echo -e "${GREEN}"
echo "==================================================================="
echo "All GUI services have been stopped."
echo "==================================================================="
echo -e "${NC}"