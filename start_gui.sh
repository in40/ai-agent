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
    local log_file=$4

    # If port is in use, try to stop the existing service first
    if check_port $port; then
        echo -e "${YELLOW}Port $port is in use, stopping existing $name...${NC}"

        # Find and kill the process using the port
        local pid=$(lsof -Pi :$port -sTCP:LISTEN -t 2>/dev/null)
        if [ -n "$pid" ]; then
            echo -e "${YELLOW}Stopping existing process (PID: $pid) on port $port...${NC}"
            kill -TERM $pid 2>/dev/null

            # Wait a moment to allow graceful shutdown
            sleep 2

            # Check if process is still running and force kill if necessary
            if kill -0 $pid 2>/dev/null; then
                echo -e "${YELLOW}Force stopping process (PID: $pid)...${NC}"
                kill -KILL $pid 2>/dev/null
            fi
        fi

        # Wait a bit more to ensure the port is released
        sleep 2
    fi

    echo -e "${GREEN}Starting $name on port $port...${NC}"
    nohup $cmd > $log_file 2>&1 &

    # Different sleep times for different services
    if [[ "$name" == "React Editor" ]]; then
        sleep 15  # React takes longer to start
    else
        sleep 5  # Standard time for other services
    fi

    if check_port $port; then
        echo -e "${GREEN}$name successfully started on port $port${NC}"
        return 0
    else
        echo -e "${RED}Failed to start $name on port $port${NC}"
        return 1
    fi
}

# Change to the project root directory
cd "$(dirname "$0")"

# Activate the virtual environment
source ai_agent_env/bin/activate

# Start the Workflow API server (port 5001)
start_service "./start_workflow_api.sh" "Workflow API" "5001" "workflow_api.log"

# Start the React Editor (port 3000) - only if npm is available
if command -v npm &> /dev/null; then
    start_service "./start_react_gui.sh" "React Editor" "3000" "react_server.log"
else
    echo -e "${YELLOW}Warning: npm not found, skipping React Editor startup${NC}"
fi

# Start the main GUI server (port 8000)
start_service "python gui/server.py" "Main Dashboard" "8000" "gui_server.log"

# Start the Streamlit editor (port 8501) - binding to all interfaces
start_service "streamlit run gui/enhanced_streamlit_app.py --server.port 8501 --server.address 0.0.0.0 --server.headless true" "Streamlit Editor" "8501" "streamlit_server.log"

echo -e "${GREEN}"
echo "==================================================================="
echo "LangGraph Visual Editor GUI components are now running:"
echo "- Workflow API: http://$(hostname -I | awk '{print $1}'):5001 or http://localhost:5001"
echo "- React Editor: http://$(hostname -I | awk '{print $1}'):3000 or http://localhost:3000"
echo "- Main Dashboard: http://$(hostname -I | awk '{print $1}'):8000 or http://localhost:8000"
echo "- Streamlit Editor: http://$(hostname -I | awk '{print $1}'):8501 or http://localhost:8501"
echo "==================================================================="
echo -e "${NC}"

# Exit the script after starting all services
exit 0