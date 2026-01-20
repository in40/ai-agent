#!/bin/bash

# Script to start GUI components for the LangGraph Visual Editor

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting LangGraph Visual Editor GUI components...${NC}"

# Function to check if a port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Function to start a service in background
start_service() {
    local cmd=$1
    local name=$2
    local port=$3
    
    if check_port $port; then
        echo -e "${YELLOW}Warning: Port $port is already in use, skipping $name${NC}"
        return 1
    else
        echo -e "${GREEN}Starting $name on port $port...${NC}"
        eval "$cmd" &
        sleep 3  # Give the service time to start
        
        if check_port $port; then
            echo -e "${GREEN}$name successfully started on port $port${NC}"
            return 0
        else
            echo -e "${RED}Failed to start $name on port $port${NC}"
            return 1
        fi
    fi
}

# Change to the project root directory
cd "$(dirname "$0")"

# Start the main GUI server (port 8000)
start_service "python gui/server.py" "Main Dashboard" "8000"

# Start the Streamlit editor (port 8501)
start_service "streamlit run gui/enhanced_streamlit_app.py --server.port 8501 --server.headless true" "Streamlit Editor" "8501"

echo -e "${GREEN}"
echo "==================================================================="
echo "LangGraph Visual Editor GUI components are now running:"
echo "- Main Dashboard: http://localhost:8000"
echo "- Streamlit Editor: http://localhost:8501"
echo ""
echo "Note: To start the React Editor (port 3000), navigate to"
echo "      gui/react_editor and run 'npm start'"
echo "==================================================================="
echo -e "${NC}"

# Keep the script running
wait