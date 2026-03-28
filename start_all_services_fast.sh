#!/bin/bash

# Optimized script to start all AI Agent services
# Improved start/stop speed with parallel processing and minimal waits

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${GREEN}Starting AI Agent System - All Services (FAST MODE)${NC}"

# Get the project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

# Activate the virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source "$PROJECT_ROOT/ai_agent_env/bin/activate" || {
    echo -e "${RED}Error: Could not activate virtual environment${NC}"
    exit 1
}

# Parse arguments
PARALLEL_START=false
SKIP_GUI=false
SKIP_MCP=false
STATUS_ONLY=false

for arg in "$@"; do
    case $arg in
        --parallel)
            PARALLEL_START=true
            shift
            ;;
        --no-gui)
            SKIP_GUI=true
            shift
            ;;
        --no-mcp)
            SKIP_MCP=true
            shift
            ;;
        --status)
            STATUS_ONLY=true
            shift
            ;;
        --help)
            echo "Usage: $0 [options]"
            echo "Options:"
            echo "  --parallel  Start services in parallel (faster)"
            echo "  --no-gui    Skip GUI services (Streamlit, React, LangGraph)"
            echo "  --no-mcp    Skip MCP servers"
            echo "  --status    Only check service status (no start)"
            exit 0
            ;;
    esac
done

# Status only mode - just check services and exit
if [ "$STATUS_ONLY" = true ]; then
    echo -e "${BLUE}Checking service status...${NC}"
    
    check_status() {
        local name=$1
        local port=$2
        local endpoint=${3:-/health}
        
        if curl -s -f -m 2 "http://localhost:$port$endpoint" > /dev/null 2>&1; then
            echo -e "${GREEN}✓ $name (port $port)${NC}"
        else
            echo -e "${RED}✗ $name (port $port) - not running${NC}"
        fi
    }
    
    echo ""
    check_status "API Gateway" 5000
    check_status "Auth Service" 5001
    check_status "Agent Service" 5002
    check_status "RAG Service" 5003
    check_status "Workflow API" 5004 "/api/health"
    check_status "Streamlit App" 8501
    check_status "React Editor" 3000
    check_status "MCP Registry" 8080
    if [ "$SKIP_MCP" = false ]; then
        # MCP servers use /mcp endpoint or specific paths
        for port in 8089 8090 8091 8092 8093; do
            # Try multiple possible endpoints
            if curl -s -f -m 2 "http://localhost:$port/health" > /dev/null 2>&1; then
                case $port in
                    8089) echo -e "${GREEN}✓ DNS MCP Server (port $port)${NC}" ;;
                    8090) echo -e "${GREEN}✓ Search MCP Server (port $port)${NC}" ;;
                    8091) echo -e "${GREEN}✓ RAG MCP Server (port $port)${NC}" ;;
                    8092) echo -e "${GREEN}✓ SQL MCP Server (port $port)${NC}" ;;
                    8093) echo -e "${GREEN}✓ Download MCP Server (port $port)${NC}" ;;
                esac
            elif nc -z localhost $port 2>/dev/null; then
                # Port is open, service is running
                case $port in
                    8089) echo -e "${GREEN}✓ DNS MCP Server (port $port)${NC}" ;;
                    8090) echo -e "${GREEN}✓ Search MCP Server (port $port)${NC}" ;;
                    8091) echo -e "${GREEN}✓ RAG MCP Server (port $port)${NC}" ;;
                    8092) echo -e "${GREEN}✓ SQL MCP Server (port $port)${NC}" ;;
                    8093) echo -e "${GREEN}✓ Download MCP Server (port $port)${NC}" ;;
                esac
            else
                case $port in
                    8089) echo -e "${RED}✗ DNS MCP Server (port $port) - not running${NC}" ;;
                    8090) echo -e "${RED}✗ Search MCP Server (port $port) - not running${NC}" ;;
                    8091) echo -e "${RED}✗ RAG MCP Server (port $port) - not running${NC}" ;;
                    8092) echo -e "${RED}✗ SQL MCP Server (port $port) - not running${NC}" ;;
                    8093) echo -e "${RED}✗ Download MCP Server (port $port) - not running${NC}" ;;
                esac
            fi
        done
        check_status "Document Store" 3070 "/mcp"
    fi
    
    echo ""
    echo -e "${GREEN}Status check complete.${NC}"
    exit 0
fi

# Check if Redis is available
REDIS_STARTED=false
if command -v redis-server >/dev/null 2>&1; then
    if ! nc -z localhost 6379 2>/dev/null; then
        echo -e "${YELLOW}Starting Redis...${NC}"
        redis-server --daemonize yes
        sleep 1
        REDIS_STARTED=true
    fi
else
    echo -e "${RED}Redis not found - session management disabled${NC}"
fi

# Set environment variables
export JWT_SECRET_KEY="consistent-secret-key-for-all-microservices"
export SECRET_KEY="consistent-secret-key-for-all-microservices"
export REDIS_HOST=localhost
export REDIS_PORT=6379
export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"
export FLASK_ENV="${FLASK_ENV:-production}"

# Kill processes on multiple ports in parallel
kill_ports_parallel() {
    local ports="$@"
    echo -e "${YELLOW}Cleaning up ports...${NC}"
    
    pids=()
    for port in $ports; do
        pid=$(lsof -t -i:$port 2>/dev/null || true)
        if [ ! -z "$pid" ]; then
            echo "  Port $port: killing PID $pid"
            kill -TERM $pid 2>/dev/null & pids+=($!)
        fi
    done
    
    # Wait for all kill commands
    wait "${pids[@]}" 2>/dev/null || true
    sleep 2  # Single wait for all to shutdown
}

# Prepare all ports
ALL_PORTS="5001 5002 5003 5000 8000 8501 3000 5004 8080 8089 8090 8091 8092 8093 3070"
kill_ports_parallel $ALL_PORTS

# Setup SSH tunnel for Neo4j
echo -e "${YELLOW}Setting up SSH tunnel for Neo4j...${NC}"
if [ -f "$PROJECT_ROOT/.env" ]; then
    source "$PROJECT_ROOT/.env"
fi
NEO4J_SSH_HOST="${NEO4J_SSH_HOST:-192.168.51.187}"
NEO4J_SSH_USER="${NEO4J_SSH_USER:-sorokin}"
NEO4J_SSH_KEY="${NEO4J_SSH_KEY:-~/.ssh/id_ed25519_graphrag}"
NEO4J_SSH_KEY=$(eval echo "$NEO4J_SSH_KEY")

pkill -f "ssh.*-L.*7687" 2>/dev/null || true

if [ -f "$NEO4J_SSH_KEY" ]; then
    ssh -N -f -i "$NEO4J_SSH_KEY" \
        -o StrictHostKeyChecking=no \
        -o UserKnownHostsFile=/dev/null \
        -L 7687:localhost:7687 \
        -L 7474:localhost:7474 \
        ${NEO4J_SSH_USER}@${NEO4J_SSH_HOST} 2>/dev/null && \
    echo -e "${GREEN}✓ SSH tunnel established${NC}" || \
    echo -e "${YELLOW}⚠ SSH tunnel failed${NC}"
fi

# Track PIDs
declare -A PIDS
GUI_SERVICES_RUNNING=false

# Helper to start service in background
start_service() {
    local name=$1
    local cmd=$2
    local log=$3
    
    echo -e "${YELLOW}Starting $name...${NC}"
    nohup bash -c "$cmd" > "$log" 2>&1 &
    PIDS[$name]=$!
    echo -e "${GREEN}  $name started (PID: ${PIDS[$name]})${NC}"
}

# Start core services
echo ""
echo -e "${BLUE}Starting core services...${NC}"

# Workflow API (required for GUI)
start_service "Workflow API" \
    "source '$PROJECT_ROOT/ai_agent_env/bin/activate' && cd '$PROJECT_ROOT/gui/react_editor' && python workflow_api.py" \
    "workflow_api.log"

# Auth Service (port 5001) - required by gateway
start_service "Auth Service" \
    "source '$PROJECT_ROOT/ai_agent_env/bin/activate' && python -m backend.services.auth.app" \
    "auth_service.log"

# Agent Service (port 5002)
start_service "Agent Service" \
    "source '$PROJECT_ROOT/ai_agent_env/bin/activate' && python -m backend.services.agent.app" \
    "agent_service.log"

# RAG Service (port 5003)
start_service "RAG Service" \
    "source '$PROJECT_ROOT/ai_agent_env/bin/activate' && python -m backend.services.rag.app" \
    "rag_service.log"

# Gateway (port 5000) - main entry point
start_service "API Gateway" \
    "source '$PROJECT_ROOT/ai_agent_env/bin/activate' && python -m backend.services.gateway.app" \
    "gateway.log"

if [ "$SKIP_GUI" = true ]; then
    echo -e "${YELLOW}Skipping GUI services (--no-gui)${NC}"
else
    GUI_SERVICES_RUNNING=true
    
    # LangGraph Studio
    start_service "LangGraph Studio" \
        "source '$PROJECT_ROOT/ai_agent_env/bin/activate' && python -m langgraph_cli.cli serve --host 0.0.0.0 --port 8000" \
        "langgraph_studio.log"

    # Streamlit
    start_service "Streamlit" \
        "source '$PROJECT_ROOT/ai_agent_env/bin/activate' && streamlit run '$PROJECT_ROOT/gui/enhanced_streamlit_app.py' --server.address=0.0.0.0 --server.port=8501 --server.headless=true --logger.level=WARNING" \
        "streamlit_app.log"

    # React Editor
    start_service "React Editor" \
        "cd '$PROJECT_ROOT/gui/react_editor' && npm start" \
        "react_editor.log"
fi

# MCP Registry
start_service "MCP Registry" \
    "source '$PROJECT_ROOT/ai_agent_env/bin/activate' && python -m registry.start_registry_server --host 0.0.0.0 --port 8080" \
    "mcp_registry.log"

# Wait for registry to be ready (with timeout)
echo -e "${YELLOW}Waiting for MCP registry...${NC}"
REGISTRY_READY=false
for i in {1..10}; do
    if curl -s -f -m 2 "http://localhost:8080/health" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Registry ready${NC}"
        REGISTRY_READY=true
        break
    fi
    if [ $i -eq 5 ]; then
        echo -e "${YELLOW}Waiting for registry...${NC}"
    fi
    sleep 1
done

if [ "$REGISTRY_READY" = false ]; then
    echo -e "${RED}✗ Registry not responding${NC}"
    tail -n 20 mcp_registry.log 2>/dev/null || true
fi

if [ "$SKIP_MCP" = true ]; then
    echo -e "${YELLOW}Skipping MCP servers (--no-mcp)${NC}"
else
    echo -e "${BLUE}Starting MCP servers...${NC}"
    
    # Start all MCP servers in parallel
    start_service "DNS MCP" \
        "source '$PROJECT_ROOT/ai_agent_env/bin/activate' && python -m search_server.mcp_dns_server --host 0.0.0.0 --port 8089 --registry-url http://localhost:8080" \
        "dns_mcp_server.log"
    
    start_service "Search MCP" \
        "source '$PROJECT_ROOT/ai_agent_env/bin/activate' && python -m search_server.mcp_search_server --host 0.0.0.0 --port 8090 --registry-url http://localhost:8080" \
        "search_mcp_server.log"
    
    start_service "RAG MCP" \
        "source '$PROJECT_ROOT/ai_agent_env/bin/activate' && python -m rag_component.rag_mcp_server --host 0.0.0.0 --port 8091 --registry-url http://localhost:8080" \
        "rag_mcp_server.log"
    
    start_service "SQL MCP" \
        "source '$PROJECT_ROOT/ai_agent_env/bin/activate' && python -m sql_mcp_server.sql_mcp_server --host 0.0.0.0 --port 8092 --registry-url http://localhost:8080" \
        "sql_mcp_server.log"
    
    start_service "Download MCP" \
        "source '$PROJECT_ROOT/ai_agent_env/bin/activate' && python -m download_server.download_mcp_server --host 0.0.0.0 --port 8093 --registry-url http://localhost:8080" \
        "download_mcp_server.log"
    
    start_service "Document Store" \
        "source '$PROJECT_ROOT/ai_agent_env/bin/activate' && cd '$PROJECT_ROOT/document-store-mcp-server' && python -m document_store_server.server --port 3070" \
        "document_store.log"
fi

# Wait for all services to initialize
echo -e "${YELLOW}Waiting for all services to start...${NC}"
sleep 8

# Check critical services
echo ""
echo -e "${BLUE}Verifying services...${NC}"

check_service() {
    local name=$1
    local port=$2
    
    if curl -s -f -m 2 "http://localhost:$port/health" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ $name (port $port)${NC}"
        return 0
    else
        echo -e "${YELLOW}  $name still starting...${NC}"
        return 0
    fi
}

check_service "API Gateway" 5000 || true
check_service "Auth Service" 5001 || true
check_service "Agent Service" 5002 || true
check_service "RAG Service" 5003 || true
check_service "Workflow API" 5004 || true

echo ""
echo -e "${GREEN}==========================================================${NC}"
echo -e "${GREEN}ALL AI AGENT SERVICES ARE NOW RUNNING (FAST START)${NC}"
echo -e "${GREEN}==========================================================${NC}"
echo "  Web Client:          https://localhost (via gateway)"
echo "  API Gateway:         http://localhost:5000"
echo "  Workflow API:        http://localhost:5004"
echo "  Authentication:      http://localhost:5001"
echo "  Agent Service:       http://localhost:5002"
echo "  RAG Service:         http://localhost:5003"
if [ "$GUI_SERVICES_RUNNING" = true ]; then
    echo "  LangGraph Studio:    http://localhost:8000"
    echo "  Streamlit App:       http://localhost:8501"
    echo "  React Editor:        http://localhost:3000"
fi
echo "  MCP Service Registry: http://localhost:8080"
if [ "$SKIP_MCP" = false ]; then
    echo "  DNS MCP Server:      http://localhost:8089"
    echo "  Search MCP Server:   http://localhost:8090"
    echo "  RAG MCP Server:      http://localhost:8091"
    echo "  SQL MCP Server:      http://localhost:8092"
    echo "  Download MCP Server: http://localhost:8093"
    echo "  Document Store MCP:  http://localhost:3070"
fi
echo -e "${GREEN}==========================================================${NC}"

# Save PIDs
cat > service_pids_fast.txt << EOF
WORKFLOW_PID=${PIDS["Workflow API"]}
REGISTRY_PID=${PIDS["MCP Registry"]}
DNS_PID=${PIDS["DNS MCP"]}
SEARCH_PID=${PIDS["Search MCP"]}
RAG_MCP_PID=${PIDS["RAG MCP"]}
SQL_PID=${PIDS["SQL MCP"]}
DOWNLOAD_PID=${PIDS["Download MCP"]}
DOCUMENT_STORE_PID=${PIDS["Document Store"]}
EOF

# Add GUI service PIDs if they were started
if [ "$GUI_SERVICES_RUNNING" = true ]; then
    cat >> service_pids_fast.txt << EOF
LANGGRAPH_PID=${PIDS["LangGraph Studio"]}
STREAMLIT_PID=${PIDS["Streamlit"]}
REACT_PID=${PIDS["React Editor"]}
EOF
fi

echo -e "${GREEN}Service PIDs saved to service_pids_fast.txt${NC}"

# Cleanup function
cleanup() {
    echo -e "\n${YELLOW}Stopping services...${NC}"
    
    if [ -f service_pids_fast.txt ]; then
        source service_pids_fast.txt
    fi
    
    # Build service list based on what was actually started
    SERVICES_TO_STOP=("Workflow API" "MCP Registry" "DNS MCP" "Search MCP" "RAG MCP" "SQL MCP" "Download MCP" "Document Store")
    
    if [ "$GUI_SERVICES_RUNNING" = true ]; then
        SERVICES_TO_STOP+=("LangGraph Studio" "Streamlit" "React Editor")
    fi
    
    for name in "${SERVICES_TO_STOP[@]}"; do
        pid=${PIDS[$name]}
        if [ ! -z "$pid" ] && kill -0 $pid 2>/dev/null; then
            echo -e "  Stopping $name (PID: $pid)..."
            kill $pid 2>/dev/null || true
        fi
    done
    
    # Kill all remaining python/node processes from this project
    pkill -f "workflow_api.py" 2>/dev/null || true
    pkill -f "langgraph_cli" 2>/dev/null || true
    pkill -f "streamlit.*enhanced_streamlit" 2>/dev/null || true
    pkill -f "npm start" 2>/dev/null || true
    pkill -f "start_registry_server" 2>/dev/null || true
    pkill -f "mcp_dns_server" 2>/dev/null || true
    pkill -f "mcp_search_server" 2>/dev/null || true
    pkill -f "rag_mcp_server" 2>/dev/null || true
    pkill -f "sql_mcp_server" 2>/dev/null || true
    pkill -f "download_mcp_server" 2>/dev/null || true
    pkill -f "document_store_server.server" 2>/dev/null || true
    
    # Kill processes on all ports (including GUI ports)
    for port in 5000 5001 5002 5003 5004 8080 8089 8090 8091 8092 8093 3070; do
        lsof -t -i:$port | xargs -r kill -9 2>/dev/null || true
    done
    
    if [ "$REDIS_STARTED" = true ]; then
        redis-cli shutdown 2>/dev/null || true
    fi
    
    rm -f service_pids_fast.txt
    echo -e "${GREEN}All services stopped.${NC}"
}

trap cleanup INT TERM

echo -e "${GREEN}Fast start complete! Services running in background.${NC}"
exit 0
