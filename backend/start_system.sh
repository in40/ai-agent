#!/bin/bash

# Startup script for the AI Agent system with backend and frontend components

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting AI Agent System...${NC}"

# Get the project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Activate the virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source "$PROJECT_ROOT/ai_agent_env/bin/activate"

# Start the backend server in the background
echo -e "${YELLOW}Starting backend server...${NC}"
cd "$PROJECT_ROOT"
export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"
nohup python -m flask --app backend.app run --host=0.0.0.0 --port=5000 > backend.log 2>&1 &
BACKEND_PID=$!
echo -e "${GREEN}Backend server started with PID $BACKEND_PID${NC}"

# Wait a moment for the backend to start
sleep 3

# Start the required services if they're not already running
echo -e "${YELLOW}Checking required services...${NC}"

# Check if Streamlit is running
if ! nc -z localhost 8501; then
    echo -e "${YELLOW}Starting Streamlit GUI...${NC}"
    nohup streamlit run "$PROJECT_ROOT/gui/enhanced_streamlit_app.py" --server.port 8501 --server.address 0.0.0.0 --server.headless true > streamlit.log 2>&1 &
    STREAMLIT_PID=$!
    echo -e "${GREEN}Streamlit GUI started with PID $STREAMLIT_PID${NC}"
else
    echo -e "${GREEN}Streamlit GUI is already running${NC}"
fi

# Check if React is running
if ! nc -z localhost 3000; then
    echo -e "${YELLOW}Starting React GUI...${NC}"
    cd "$PROJECT_ROOT/gui/react_editor"
    nohup npm start > react.log 2>&1 &
    REACT_PID=$!
    echo -e "${GREEN}React GUI started with PID $REACT_PID${NC}"
    cd "$PROJECT_ROOT"
else
    echo -e "${GREEN}React GUI is already running${NC}"
fi

# Wait a bit more for services to start
sleep 5

echo -e "${GREEN}"
echo "=========================================================="
echo "AI AGENT SYSTEM IS NOW RUNNING"
echo "=========================================================="
echo "Backend API:           http://localhost:5000"
echo "Web Client:            https://localhost:443 (via nginx)"
echo "Streamlit GUI:         http://localhost:8501"
echo "React GUI:             http://localhost:3000"
echo "Backend API (direct):  http://localhost:5000/api/"
echo "=========================================================="
echo -e "${NC}"

# Keep the script running
echo -e "${YELLOW}Press Ctrl+C to stop the system${NC}"

# Function to handle shutdown
cleanup() {
    echo -e "\n${YELLOW}Stopping AI Agent System...${NC}"
    
    # Kill all background processes
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
    fi
    
    if [ ! -z "$STREAMLIT_PID" ]; then
        kill $STREAMLIT_PID 2>/dev/null || true
    fi
    
    if [ ! -z "$REACT_PID" ]; then
        kill $REACT_PID 2>/dev/null || true
    fi
    
    echo -e "${GREEN}System stopped.${NC}"
    exit 0
}

# Trap SIGINT and SIGTERM
trap cleanup INT TERM

# Wait indefinitely
while true; do
    sleep 1
done