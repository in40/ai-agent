#!/bin/bash
# Script to stop the MCP (Model Context Protocol) Registry Server

set -e  # Exit immediately if a command exits with a non-zero status

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
DEFAULT_PORT=8080

# Print usage information
usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -p, --port PORT    Port the registry server is running on (default: $DEFAULT_PORT)"
    echo "  --help             Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                 # Stop server on default port"
    echo "  $0 -p 8081        # Stop server on port 8081"
}

# Default values
PORT="$DEFAULT_PORT"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -p|--port)
            PORT="$2"
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

echo -e "${BLUE}Stopping MCP Registry Server on port $PORT...${NC}"

# Find and kill the registry server process
PID=$(lsof -t -i:$PORT 2>/dev/null)

if [ -z "$PID" ]; then
    echo -e "${YELLOW}No registry server process found on port $PORT${NC}"
    echo "The server may already be stopped or running on a different port."
    exit 0
fi

echo -e "${BLUE}Found registry server process $PID, stopping it...${NC}"

# Try graceful shutdown first
kill $PID

# Wait a moment for the process to stop
sleep 3

# Check if the process is still running
if ps -p $PID > /dev/null; then
    echo -e "${YELLOW}Process still running, force killing...${NC}"
    kill -9 $PID
    
    # Wait a bit more after force killing
    sleep 2
fi

# Verify the process is gone
if ! ps -p $PID > /dev/null 2>&1; then
    echo -e "${GREEN}✓ MCP Registry Server stopped successfully${NC}"
else
    echo -e "${RED}✗ Failed to stop MCP Registry Server with PID $PID${NC}" >&2
    exit 1
fi

# Check if the port is now free
if ! lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${GREEN}✓ Port $PORT is now free${NC}"
else
    echo -e "${YELLOW}⚠ Port $PORT may still be in use by another process${NC}"
fi