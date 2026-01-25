#!/bin/bash

# Script to start all AI Agent services
# This includes the microservices architecture and GUI components

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting AI Agent System - All Services${NC}"

# Get the project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

# Activate the virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source "$PROJECT_ROOT/ai_agent_env/bin/activate" || {
    echo -e "${RED}Error: Could not activate virtual environment. Please make sure it exists at $PROJECT_ROOT/ai_agent_env${NC}"
    exit 1
}

# Check if Redis is available and running
if command -v redis-server >/dev/null 2>&1; then
    if ! nc -z localhost 6379 2>/dev/null; then
        echo -e "${YELLOW}Starting Redis...${NC}"
        redis-server --daemonize yes
        sleep 2
        REDIS_STARTED=true
    else
        echo -e "${GREEN}Redis is already running${NC}"
    fi
else
    echo -e "${RED}Redis server not found. Please install Redis to use session management and rate limiting.${NC}"
    echo -e "${YELLOW}Continuing without Redis...${NC}"
fi

# Set consistent environment variables for all services
export JWT_SECRET_KEY="consistent-secret-key-for-all-microservices"
export SECRET_KEY="consistent-secret-key-for-all-microservices"
export REDIS_HOST=localhost
export REDIS_PORT=6379
export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"

# Set Flask environment - defaults to 'production' to use Gunicorn
export FLASK_ENV="${FLASK_ENV:-production}"

# Function to check if a port is available
check_port() {
    local port=$1
    if nc -z localhost $port; then
        echo "Port $port is in use"
        return 1
    else
        echo "Port $port is available"
        return 0
    fi
}

# Function to kill process on a port
kill_port() {
    local port=$1
    local pid=$(lsof -t -i:$port 2>/dev/null)
    if [ ! -z "$pid" ]; then
        echo -e "${YELLOW}Killing process on port $port (PID: $pid)...${NC}"
        kill $pid 2>/dev/null || true
        sleep 2
    fi
}

echo -e "${BLUE}Checking and preparing ports...${NC}"

# Prepare ports for services
echo "Preparing port 5001 for auth service..."
kill_port 5001

echo "Preparing port 5002 for agent service..."
kill_port 5002

echo "Preparing port 5003 for RAG service..."
kill_port 5003

echo "Preparing port 5000 for gateway..."
kill_port 5000

echo "Preparing port 8000 for LangGraph Studio..."
kill_port 8000

echo "Preparing port 8501 for Streamlit App..."
kill_port 8501

echo "Preparing port 3000 for React Editor..."
kill_port 3000

echo "Preparing port 5004 for Workflow API..."
kill_port 5004

echo "Preparing port 8080 for MCP Service Registry..."
kill_port 8080

echo "Preparing port 8089 for DNS MCP Server..."
kill_port 8089

echo "Preparing port 8090 for Search MCP Server..."
kill_port 8090

echo "Preparing port 8091 for RAG MCP Server..."
kill_port 8091

echo "Preparing port 8092 for SQL MCP Server..."
kill_port 8092

echo "Preparing port 8093 for Download MCP Server..."
kill_port 8093

# Start the workflow API in the background
echo -e "${YELLOW}Starting workflow API on port 5004...${NC}"
cd "$PROJECT_ROOT/gui/react_editor" && nohup python workflow_api.py > workflow_api.log 2>&1 &
WORKFLOW_PID=$!
echo -e "${GREEN}Workflow API started with PID $WORKFLOW_PID${NC}"

# Wait a moment for the workflow API to start
sleep 3

# Start the auth service in the background
echo -e "${YELLOW}Starting authentication service on port 5001...${NC}"
nohup python -m backend.services.auth.app > auth_service.log 2>&1 &
AUTH_PID=$!
echo -e "${GREEN}Authentication service started with PID $AUTH_PID${NC}"

# Wait a moment for the auth service to start
sleep 3

# Start the agent service in the background
echo -e "${YELLOW}Starting agent service on port 5002...${NC}"
nohup python -m backend.services.agent.app > agent_service.log 2>&1 &
AGENT_PID=$!
echo -e "${GREEN}Agent service started with PID $AGENT_PID${NC}"

# Wait a moment for the agent service to start
sleep 3

# Start the RAG service in the background
echo -e "${YELLOW}Starting RAG service on port 5003...${NC}"
nohup python -m backend.services.rag.app > rag_service.log 2>&1 &
RAG_PID=$!
echo -e "${GREEN}RAG service started with PID $RAG_PID${NC}"

# Wait a moment for the RAG service to start
sleep 3

# Start the gateway in the background
echo -e "${YELLOW}Starting API gateway on port 5000...${NC}"
nohup python -m backend.services.gateway.app > gateway.log 2>&1 &
GATEWAY_PID=$!
echo -e "${GREEN}Gateway started with PID $GATEWAY_PID${NC}"

# Wait a bit more for services to start
sleep 5

# Start LangGraph Studio (port 8000)
echo -e "${YELLOW}Starting LangGraph Studio on port 8000...${NC}"
nohup python -c "
import sys
sys.path.insert(0, '$PROJECT_ROOT')
from langgraph_cli.cli import main
if __name__ == '__main__':
    sys.argv = ['langgraph', 'serve', '--host', '0.0.0.0', '--port', '8000']
    main()
" > langgraph_studio.log 2>&1 &
LANGGRAPH_PID=$!
echo -e "${GREEN}LangGraph Studio started with PID $LANGGRAPH_PID${NC}"

# Wait for LangGraph Studio to start
sleep 3

# Start Streamlit App (port 8501)
echo -e "${YELLOW}Starting Streamlit App on port 8501...${NC}"
nohup streamlit run "$PROJECT_ROOT/gui/enhanced_streamlit_app.py" --server.address="0.0.0.0" --server.port=8501 --server.headless=true > streamlit_app.log 2>&1 &
STREAMLIT_PID=$!
echo -e "${GREEN}Streamlit App started with PID $STREAMLIT_PID${NC}"

# Wait for Streamlit to start
sleep 3

# Start React Editor (port 3000)
echo -e "${YELLOW}Starting React Editor on port 3000...${NC}"
cd "$PROJECT_ROOT/gui/react_editor" && nohup npm start > react_editor.log 2>&1 &
REACT_PID=$!
echo -e "${GREEN}React Editor started with PID $REACT_PID${NC}"

# Wait for React to start
sleep 5

# Start MCP Service Registry (port 8080)
echo -e "${YELLOW}Starting MCP Service Registry on port 8080...${NC}"
nohup python -m registry.start_registry_server --host 127.0.0.1 --port 8080 > mcp_registry.log 2>&1 &
REGISTRY_PID=$!

# Wait a moment for the registry to start
sleep 3

# Check if the registry actually started successfully
if ps -p $REGISTRY_PID > /dev/null; then
    echo -e "${GREEN}MCP Service Registry started with PID $REGISTRY_PID${NC}"

    # Test the registry briefly to ensure it's responding
    if curl -s -f -m 10 "http://127.0.0.1:8080/health" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Registry server is responding to health checks${NC}"
    else
        echo -e "${YELLOW}⚠ Registry server may still be starting up${NC}"

        # Retry after a few seconds
        sleep 5
        if curl -s -f -m 10 "http://127.0.0.1:8080/health" > /dev/null 2>&1; then
            echo -e "${GREEN}✓ Registry server is now responding to health checks${NC}"
        else
            echo -e "${RED}✗ Registry server is not responding to health checks${NC}"
            echo -e "${YELLOW}Check mcp_registry.log for more details${NC}"
        fi
    fi
else
    echo -e "${RED}✗ Failed to start MCP Service Registry${NC}"
    if [ -f mcp_registry.log ]; then
        echo -e "${RED}Last 10 lines of registry log:${NC}"
        tail -n 10 mcp_registry.log
    fi
    exit 1
fi

# Wait for registry to be fully ready
sleep 3

# Start DNS MCP Server (port 8089)
echo -e "${YELLOW}Starting DNS MCP Server on port 8089...${NC}"
nohup python -m search_server.mcp_dns_server --host 127.0.0.1 --port 8089 --registry-url http://127.0.0.1:8080 > dns_mcp_server.log 2>&1 &
DNS_PID=$!
echo -e "${GREEN}DNS MCP Server started with PID $DNS_PID${NC}"

# Wait for DNS server to start
sleep 2

# Start Search MCP Server (port 8090)
echo -e "${YELLOW}Starting Search MCP Server on port 8090...${NC}"
nohup python -m search_server.mcp_search_server --host 127.0.0.1 --port 8090 --registry-url http://127.0.0.1:8080 > search_mcp_server.log 2>&1 &
SEARCH_PID=$!
echo -e "${GREEN}Search MCP Server started with PID $SEARCH_PID${NC}"

# Wait for Search server to start
sleep 2

# Start RAG MCP Server (port 8091)
echo -e "${YELLOW}Starting RAG MCP Server on port 8091...${NC}"
nohup python -m rag_component.rag_mcp_server --host 127.0.0.1 --port 8091 --registry-url http://127.0.0.1:8080 > rag_mcp_server.log 2>&1 &
RAG_MCP_PID=$!
echo -e "${GREEN}RAG MCP Server started with PID $RAG_MCP_PID${NC}"

# Wait for RAG MCP server to start
sleep 2

# Start SQL MCP Server (port 8092)
echo -e "${YELLOW}Starting SQL MCP Server on port 8092...${NC}"
nohup python -m sql_mcp_server.sql_mcp_server --host 127.0.0.1 --port 8092 --registry-url http://127.0.0.1:8080 > sql_mcp_server.log 2>&1 &
SQL_PID=$!
echo -e "${GREEN}SQL MCP Server started with PID $SQL_PID${NC}"

# Wait for SQL server to start
sleep 3

# Start Download MCP Server (port 8093)
echo -e "${YELLOW}Starting Download MCP Server on port 8093...${NC}"
nohup python -m download_server.download_mcp_server --host 127.0.0.1 --port 8093 --registry-url http://127.0.0.1:8080 > download_mcp_server.log 2>&1 &
DOWNLOAD_PID=$!
echo -e "${GREEN}Download MCP Server started with PID $DOWNLOAD_PID${NC}"

# Wait for Download server to start
sleep 3

echo -e "${GREEN}"
echo "=========================================================="
echo "ALL AI AGENT SERVICES ARE NOW RUNNING"
echo "=========================================================="
echo "Web Client:          https://192.168.51.138 (via gateway)"
echo "API Gateway:         http://192.168.51.138:5000"
echo "Workflow API:        http://192.168.51.138:5004"
echo "Authentication:      http://192.168.51.138:5001"
echo "Agent Service:       http://192.168.51.138:5002"
echo "RAG Service:         http://192.168.51.138:5003"
echo "LangGraph Studio:    http://192.168.51.138:8000"
echo "Streamlit App:       http://192.168.51.138:8501"
echo "React Editor:        http://192.168.51.138:3000"
echo "MCP Service Registry: http://192.168.51.138:8080"
echo "DNS MCP Server:      http://192.168.51.138:8089"
echo "Search MCP Server:   http://192.168.51.138:8090"
echo "RAG MCP Server:      http://192.168.51.138:8091"
echo "SQL MCP Server:      http://192.168.51.138:8092"
echo "Download MCP Server: http://192.168.51.138:8093"
echo "=========================================================="
echo -e "${NC}"

# Save PIDs to a file for later use
cat > service_pids.txt << EOF
WORKFLOW_PID=$WORKFLOW_PID
AUTH_PID=$AUTH_PID
AGENT_PID=$AGENT_PID
RAG_PID=$RAG_PID
GATEWAY_PID=$GATEWAY_PID
LANGGRAPH_PID=$LANGGRAPH_PID
STREAMLIT_PID=$STREAMLIT_PID
REACT_PID=$REACT_PID
REGISTRY_PID=$REGISTRY_PID
DNS_PID=$DNS_PID
SEARCH_PID=$SEARCH_PID
RAG_MCP_PID=$RAG_MCP_PID
SQL_PID=$SQL_PID
DOWNLOAD_PID=$DOWNLOAD_PID
EOF

echo -e "${GREEN}Service PIDs saved to service_pids.txt${NC}"

# Function to handle shutdown
cleanup() {
    echo -e "\n${YELLOW}Stopping all AI Agent services...${NC}"

    # Read PIDs from file
    if [ -f service_pids.txt ]; then
        source service_pids.txt
    fi

    # Kill all background processes
    for pid_var in WORKFLOW_PID AUTH_PID AGENT_PID RAG_PID GATEWAY_PID LANGGRAPH_PID STREAMLIT_PID REACT_PID REGISTRY_PID DNS_PID SEARCH_PID RAG_MCP_PID SQL_PID DOWNLOAD_PID; do
        pid_val=${!pid_var}
        if [ ! -z "$pid_val" ] && kill -0 $pid_val 2>/dev/null; then
            echo -e "${YELLOW}Stopping $pid_var (PID: $pid_val)...${NC}"
            kill $pid_val 2>/dev/null || true
        fi
    done

    # Stop Redis if we started it
    if [ "$REDIS_STARTED" = true ]; then
        if command -v redis-cli >/dev/null 2>&1; then
            echo -e "${YELLOW}Stopping Redis...${NC}"
            redis-cli shutdown 2>/dev/null || true
        fi
    fi

    # Remove PID file
    rm -f service_pids.txt

    echo -e "${GREEN}All services stopped.${NC}"
    exit 0
}

# Trap SIGINT and SIGTERM
trap cleanup INT TERM

echo -e "${YELLOW}All services started successfully and are running in the background.${NC}"

# Exit the script, leaving services running in background
exit 0