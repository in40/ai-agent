#!/bin/bash
# Stop all services started by start_all_services_fast.sh

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}Stopping AI Agent services...${NC}"

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

# Source PIDs
if [ -f service_pids_fast.txt ]; then
    source service_pids_fast.txt
fi

# Kill by PID
for name in "Workflow API" "LangGraph Studio" "Streamlit" "React Editor" \
            "MCP Registry" "DNS MCP" "Search MCP" "RAG MCP" "SQL MCP" \
            "Download MCP" "Document Store"; do
    pid_var="${name// /_}_PID"  # Convert "Workflow API" to "WORKFLOW_API_PID"
    pid=${!pid_var}
    if [ ! -z "$pid" ] && kill -0 "$pid" 2>/dev/null; then
        echo "Stopping $name (PID: $pid)..."
        kill "$pid" 2>/dev/null || true
    fi
done

# Kill processes by name patterns
pkill -f "workflow_api.py" 2>/dev/null || true
pkill -f "langgraph_cli.cli serve" 2>/dev/null || true
pkill -f "streamlit.*enhanced_streamlit" 2>/dev/null || true
pkill -f "npm start" 2>/dev/null || true
pkill -f "start_registry_server" 2>/dev/null || true
pkill -f "mcp_dns_server" 2>/dev/null || true
pkill -f "mcp_search_server" 2>/dev/null || true
pkill -f "rag_mcp_server" 2>/dev/null || true
pkill -f "sql_mcp_server" 2>/dev/null || true
pkill -f "download_mcp_server" 2>/dev/null || true
pkill -f "document_store_server.server" 2>/dev/null || true
pkill -f "backend.services.auth.app" 2>/dev/null || true
pkill -f "backend.services.agent.app" 2>/dev/null || true
pkill -f "backend.services.rag.app" 2>/dev/null || true
pkill -f "backend.services.gateway.app" 2>/dev/null || true

# Kill processes on service ports
for port in 5000 5001 5002 5003 5004 8080 8089 8090 8091 8092 8093 3070 8000 8501 3000; do
    lsof -t -i:$port 2>/dev/null | xargs -r kill -9 2>/dev/null || true
done

# Stop Redis if running
if command -v redis-cli >/dev/null 2>&1; then
    nc -z localhost 6379 2>/dev/null && redis-cli shutdown 2>/dev/null || true
fi

# Clean up
rm -f service_pids_fast.txt

echo -e "${GREEN}All services stopped.${NC}"
