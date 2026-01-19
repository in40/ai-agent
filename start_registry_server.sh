#!/bin/bash
# Script to start the MCP (Model Context Protocol) Registry Server

set -e  # Exit immediately if a command exits with a non-zero status

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
DEFAULT_PORT=8080
DEFAULT_HOST="127.0.0.1"
DEFAULT_VENV_PATH="./ai_agent_env"

# Print usage information
usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -p, --port PORT       Port to run the registry server on (default: $DEFAULT_PORT)"
    echo "  -h, --host HOST       Host to bind the registry server to (default: $DEFAULT_HOST)"
    echo "  -v, --venv PATH       Path to Python virtual environment (default: $DEFAULT_VENV_PATH)"
    echo "  -l, --log-file FILE   Log file path (default: registry_server.log)"
    echo "  --help                Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                                    # Start with default settings"
    echo "  $0 -p 8081                           # Start on port 8081"
    echo "  $0 -h 0.0.0.0 -p 9090              # Bind to all interfaces on port 9090"
}

# Default values
PORT="$DEFAULT_PORT"
HOST="$DEFAULT_HOST"
VENV_PATH="$DEFAULT_VENV_PATH"
LOG_FILE="registry_server.log"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -p|--port)
            PORT="$2"
            shift 2
            ;;
        -h|--host)
            HOST="$2"
            shift 2
            ;;
        -v|--venv)
            VENV_PATH="$2"
            shift 2
            ;;
        -l|--log-file)
            LOG_FILE="$2"
            shift 2
            ;;
        --help)
            usage
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}" >&2
            usage
            exit 1
            ;;
    esac
done

echo -e "${BLUE}Starting MCP Registry Server${NC}"
echo "==============================="

# Check if virtual environment exists
if [ ! -d "$VENV_PATH" ]; then
    echo -e "${RED}Error: Virtual environment not found at $VENV_PATH${NC}" >&2
    echo "Please create the virtual environment first."
    exit 1
fi

# Activate virtual environment
echo -e "${BLUE}Activating virtual environment...${NC}"
source "$VENV_PATH/bin/activate"

# Check if registry module exists
if ! python -c "import registry.start_registry_server" 2>/dev/null; then
    echo -e "${RED}Error: Registry module not found${NC}" >&2
    echo "Make sure the registry module is properly installed in your environment."
    exit 1
fi

# Check if port is already in use
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${RED}Error: Port $PORT is already in use${NC}" >&2
    echo "Please stop the process using this port or choose a different port."
    exit 1
fi

echo -e "${BLUE}Starting MCP Registry Server on $HOST:$PORT...${NC}"

# Start the registry server in the background and redirect output to log file
nohup python -m registry.start_registry_server --host "$HOST" --port "$PORT" > "$LOG_FILE" 2>&1 &

# Get the PID of the background process
REGISTRY_SERVER_PID=$!

# Wait a moment for the server to start
sleep 3

# Check if the server is running
if ps -p $REGISTRY_SERVER_PID > /dev/null; then
    echo -e "${GREEN}MCP Registry Server started with PID: $REGISTRY_SERVER_PID${NC}"
    echo -e "${GREEN}MCP Registry Server is running on $HOST:$PORT${NC}"
    echo "Check $LOG_FILE for server output"
    
    # Test the server briefly
    if curl -s -f -m 5 "http://$HOST:$PORT/health" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Registry server is responding to health checks${NC}"
    else
        echo -e "${YELLOW}⚠ Registry server may still be starting up${NC}"
    fi
else
    echo -e "${RED}Error: Failed to start MCP Registry Server${NC}" >&2
    # Show the last few lines of the log if startup failed
    if [ -f "$LOG_FILE" ]; then
        echo -e "${RED}Last 10 lines of log:${NC}"
        tail -n 10 "$LOG_FILE"
    fi
    exit 1
fi