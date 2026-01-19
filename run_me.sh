#!/bin/bash

# Script to run the AI agent with MCP services
# Starts MCP registry and servers in background
# Runs the main AI agent application
# Cleans up and stops all services on exit

set -e  # Exit on any error

# Load environment variables from .env file if it exists
if [ -f ".env" ]; then
    echo "Loading environment variables from .env file..."
    export $(grep -v '^#' .env | xargs)
else
    echo "Warning: .env file not found. Please copy .env.example to .env and configure your settings."
    echo "For MCP services to work properly, you may need to set:"
    echo "- BRAVE_SEARCH_API_KEY for web search functionality"
    echo "- Database connection parameters"
    echo "- LLM provider configurations"
fi

# Explicitly set screen logging to true to enable logging but with heartbeat filtering
export ENABLE_SCREEN_LOGGING=true

# Set environment variable to enable interactive mode which suppresses heartbeat logs during user input
export INTERACTIVE_MODE=true

# Ensure required environment variables are set
if [ -z "$BRAVE_SEARCH_API_KEY" ]; then
    echo "Warning: BRAVE_SEARCH_API_KEY is not set. Web search functionality will not work properly."
    echo "Please set this variable in your .env file to enable web search."
fi

# Variables to store process IDs
MCP_REGISTRY_PID=""
DNS_SERVER_PID=""
WEB_SEARCH_SERVER_PID=""
RAG_SERVER_PID=""
SQL_SERVER_PID=""

# Function to cleanup background processes
cleanup() {
    echo "Shutting down services..."

    if [ ! -z "$MCP_REGISTRY_PID" ] && kill -0 "$MCP_REGISTRY_PID" 2>/dev/null; then
        echo "Stopping MCP registry (PID: $MCP_REGISTRY_PID)"
        kill "$MCP_REGISTRY_PID"
    fi

    if [ ! -z "$DNS_SERVER_PID" ] && kill -0 "$DNS_SERVER_PID" 2>/dev/null; then
        echo "Stopping DNS resolution MCP server (PID: $DNS_SERVER_PID)"
        kill "$DNS_SERVER_PID"
    fi

    if [ ! -z "$WEB_SEARCH_SERVER_PID" ] && kill -0 "$WEB_SEARCH_SERVER_PID" 2>/dev/null; then
        echo "Stopping Web search MCP server (PID: $WEB_SEARCH_SERVER_PID)"
        kill "$WEB_SEARCH_SERVER_PID"
    fi

    if [ ! -z "$RAG_SERVER_PID" ] && kill -0 "$RAG_SERVER_PID" 2>/dev/null; then
        echo "Stopping RAG MCP server (PID: $RAG_SERVER_PID)"
        kill "$RAG_SERVER_PID"
    fi

    if [ ! -z "$SQL_SERVER_PID" ] && kill -0 "$SQL_SERVER_PID" 2>/dev/null; then
        echo "Stopping SQL MCP server (PID: $SQL_SERVER_PID)"
        kill "$SQL_SERVER_PID"
    fi

    # Wait a bit for processes to terminate gracefully
    sleep 2

    # Force kill if still running
    if [ ! -z "$MCP_REGISTRY_PID" ] && kill -0 "$MCP_REGISTRY_PID" 2>/dev/null; then
        echo "Force stopping MCP registry"
        kill -9 "$MCP_REGISTRY_PID" 2>/dev/null || true
    fi

    if [ ! -z "$DNS_SERVER_PID" ] && kill -0 "$DNS_SERVER_PID" 2>/dev/null; then
        echo "Force stopping DNS resolution MCP server"
        kill -9 "$DNS_SERVER_PID" 2>/dev/null || true
    fi

    if [ ! -z "$WEB_SEARCH_SERVER_PID" ] && kill -0 "$WEB_SEARCH_SERVER_PID" 2>/dev/null; then
        echo "Force stopping Web search MCP server"
        kill -9 "$WEB_SEARCH_SERVER_PID" 2>/dev/null || true
    fi

    if [ ! -z "$RAG_SERVER_PID" ] && kill -0 "$RAG_SERVER_PID" 2>/dev/null; then
        echo "Force stopping RAG MCP server"
        kill -9 "$RAG_SERVER_PID" 2>/dev/null || true
    fi

    if [ ! -z "$SQL_SERVER_PID" ] && kill -0 "$SQL_SERVER_PID" 2>/dev/null; then
        echo "Force stopping SQL MCP server"
        kill -9 "$SQL_SERVER_PID" 2>/dev/null || true
    fi

    # Clean up the temporary log file
    if [ -f "$BACKGROUND_LOG_FILE" ]; then
        rm "$BACKGROUND_LOG_FILE"
    fi

    echo "All services stopped."
}

# Set trap to ensure cleanup happens on exit
trap cleanup EXIT INT TERM

# Function to check if registry is already running
check_registry_running() {
    # Use Python to check if port 8080 is in use
    python3 -c "
import socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
result = s.connect_ex(('127.0.0.1', 8080))
s.close()
exit(0 if result == 0 else 1)
" 2>/dev/null
    return $?
}

# Function to stop any existing registry process
stop_existing_registry() {
    # Find and kill any existing registry process using port 8080
    if command -v lsof >/dev/null 2>&1; then
        # Use lsof to find the process using port 8080
        PID=$(lsof -ti:8080)
        if [ ! -z "$PID" ]; then
            echo "Found existing process on port 8080 (PID: $PID), stopping it..."
            kill -9 $PID 2>/dev/null || true
            sleep 2  # Wait for the process to terminate
        fi
    elif command -v ss >/dev/null 2>&1; then
        # Use ss as an alternative to lsof
        PID=$(ss -tulnp | grep ':8080' | awk '{print $7}' | cut -d',' -f1 | cut -d'=' -f2)
        if [ ! -z "$PID" ]; then
            echo "Found existing process on port 8080 (PID: $PID), stopping it..."
            kill -9 $PID 2>/dev/null || true
            sleep 2  # Wait for the process to terminate
        fi
    else
        # Fallback: try to find Python processes that might be the registry
        PIDS=$(pgrep -f "start_registry_server\|service_registry")
        if [ ! -z "$PIDS" ]; then
            echo "Found potential registry processes (PIDs: $PIDS), stopping them..."
            kill -9 $PIDS 2>/dev/null || true
            sleep 2  # Wait for the processes to terminate
        fi
    fi
}

# Check if registry is already running before starting
if check_registry_running; then
    echo "MCP registry appears to be running on port 8080"
    stop_existing_registry
    # Double-check after stopping
    if check_registry_running; then
        echo "MCP registry is still running on port 8080"
        echo "Please stop the existing registry server manually"
        exit 1
    fi
fi

# Create a temporary log file for background services
BACKGROUND_LOG_FILE=$(mktemp)

echo "Starting MCP registry..."
python -m registry.start_registry_server >"$BACKGROUND_LOG_FILE" 2>&1 &
MCP_REGISTRY_PID=$!
echo "MCP registry started with PID: $MCP_REGISTRY_PID"

# Give the registry a moment to start
sleep 3

# Check if registry is running
if ! kill -0 "$MCP_REGISTRY_PID" 2>/dev/null; then
    echo "ERROR: MCP registry failed to start"
    # Show the log if there was an error
    if [ -f "$BACKGROUND_LOG_FILE" ]; then
        cat "$BACKGROUND_LOG_FILE"
    fi
    exit 1
fi

# Start DNS resolution MCP server in background
echo "Starting DNS resolution MCP server..."
python -m search_server.mcp_dns_server >>"$BACKGROUND_LOG_FILE" 2>&1 &
DNS_SERVER_PID=$!
echo "DNS resolution MCP server started with PID: $DNS_SERVER_PID"

# Give the server a moment to start
sleep 3

# Check if DNS server is running
if ! kill -0 "$DNS_SERVER_PID" 2>/dev/null; then
    echo "ERROR: DNS resolution MCP server failed to start"
    # Show the log if there was an error
    if [ -f "$BACKGROUND_LOG_FILE" ]; then
        cat "$BACKGROUND_LOG_FILE"
    fi
    exit 1
fi

# Start Web search MCP server in background
echo "Starting Web search MCP server..."
python -m search_server.mcp_search_server >>"$BACKGROUND_LOG_FILE" 2>&1 &
WEB_SEARCH_SERVER_PID=$!
echo "Web search MCP server started with PID: $WEB_SEARCH_SERVER_PID"

# Give the server a moment to start
sleep 3

# Check if Web search server is running
if ! kill -0 "$WEB_SEARCH_SERVER_PID" 2>/dev/null; then
    echo "ERROR: Web search MCP server failed to start"
    # Show the log if there was an error
    if [ -f "$BACKGROUND_LOG_FILE" ]; then
        cat "$BACKGROUND_LOG_FILE"
    fi
    exit 1
fi

# Start RAG MCP server in background
echo "Starting RAG MCP server..."
python -m rag_component.rag_mcp_server --host 127.0.0.1 --port 8091 --registry-url http://127.0.0.1:8080 >>"$BACKGROUND_LOG_FILE" 2>&1 &
RAG_SERVER_PID=$!
echo "RAG MCP server started with PID: $RAG_SERVER_PID"

# Give the server a moment to start
sleep 3

# Check if RAG server is running
if ! kill -0 "$RAG_SERVER_PID" 2>/dev/null; then
    echo "ERROR: RAG MCP server failed to start"
    # Show the log if there was an error
    if [ -f "$BACKGROUND_LOG_FILE" ]; then
        cat "$BACKGROUND_LOG_FILE"
    fi
    exit 1
fi

# Start SQL MCP server in background
echo "Starting SQL MCP server..."
python -m sql_mcp_server.sql_mcp_server --host 127.0.0.1 --port 8092 --registry-url http://127.0.0.1:8080 >>"$BACKGROUND_LOG_FILE" 2>&1 &
SQL_SERVER_PID=$!
echo "SQL MCP server started with PID: $SQL_SERVER_PID"

# Give the server a moment to start
sleep 3

# Check if SQL server is running
if ! kill -0 "$SQL_SERVER_PID" 2>/dev/null; then
    echo "ERROR: SQL MCP server failed to start"
    # Show the log if there was an error
    if [ -f "$BACKGROUND_LOG_FILE" ]; then
        cat "$BACKGROUND_LOG_FILE"
    fi
    exit 1
fi

echo "All MCP services are running."

# Run the main AI agent application with registry URL
echo "Starting main AI agent application..."
python -m core.main --registry-url http://127.0.0.1:8080

echo "Main application exited."

# The trap will handle cleanup when the script exits