#!/bin/bash
# Master script to start all LangGraph Editor services

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting all LangGraph Editor services...${NC}"

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

    if check_port $port; then
        echo -e "${YELLOW}Warning: Port $port is already in use, skipping $name${NC}"
        return 1
    else
        echo -e "${GREEN}Starting $name on port $port...${NC}"
        # Run the service with output redirected to log files to prevent interference
        nohup $cmd > $log_file 2>&1 &
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

# Start React development server in the background
start_service "/root/qwen_test/ai_agent/start_react_editor.sh" "React Editor" "3000" "react_server.log"

# Wait a moment for the React server to start
sleep 5

# Start Streamlit application in the background
start_service "/root/qwen_test/ai_agent/start_streamlit.sh" "Streamlit App" "8501" "streamlit_server.log"

# Wait a moment for the Streamlit server to start
sleep 5

# Start LangGraph Studio server in the background
start_service "/root/qwen_test/ai_agent/start_langgraph_studio.sh" "LangGraph Studio" "8000" "langgraph_server.log"

# Wait a moment for the LangGraph Studio server to start
sleep 5

# Start Workflow API server in the background
start_service "cd /root/qwen_test/ai_agent/gui/react_editor && source ../../ai_agent_env/bin/activate && python3 workflow_api.py" "Workflow API" "5001" "workflow_api.log"
sleep 3  # Wait a moment for the Workflow API server to start

echo -e "${GREEN}"
echo "==================================================================="
echo "All services started successfully!"
echo "React Editor: http://$(hostname -I | awk '{print $1}'):3000 or http://localhost:3000"
echo "Streamlit App: http://$(hostname -I | awk '{print $1}'):8501 or http://localhost:8501"
echo "LangGraph Studio: http://$(hostname -I | awk '{print $1}'):8000 or http://localhost:8000"
echo "Workflow API: http://$(hostname -I | awk '{print $1}'):5001 or http://localhost:5001"
echo "==================================================================="
echo -e "${NC}"

# Exit the script after starting all services
exit 0