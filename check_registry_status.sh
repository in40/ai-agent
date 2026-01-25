#!/bin/bash
# Script to check the status of the MCP (Model Context Protocol) Registry Server

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

# Print usage information
usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -p, --port PORT       Port the registry server is running on (default: $DEFAULT_PORT)"
    echo "  -h, --host HOST       Host the registry server is running on (default: $DEFAULT_HOST)"
    echo "  --help                Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                                    # Check status on default host:port"
    echo "  $0 -p 8081                           # Check status on port 8081"
    echo "  $0 -h 0.0.0.0 -p 9090              # Check status on specific host:port"
}

# Default values
PORT="$DEFAULT_PORT"
HOST="$DEFAULT_HOST"

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

echo -e "${BLUE}Checking MCP Registry Server Status${NC}"
echo "=================================="

# Check if the registry server process is running
if command -v lsof >/dev/null 2>&1; then
    PID=$(lsof -t -i:$PORT 2>/dev/null)
elif command -v ss >/dev/null 2>&1; then
    PID=$(ss -tulnp | grep ":$PORT " | awk '{for(i=1;i<=NF;i++) if($i ~ /pid/) print substr($i,5)}' 2>/dev/null)
elif command -v netstat >/dev/null 2>&1; then
    PID=$(netstat -tulnp 2>/dev/null | grep ":$PORT " | awk '/LISTEN/ {match($NF, /[0-9]+/); print substr($NF, RSTART, RLENGTH)}')
else
    echo -e "${RED}Error: No network utility found (lsof, ss, or netstat)${NC}" >&2
    exit 1
fi

# If PID is empty, try to get it differently
if [ -z "$PID" ]; then
    # Use lsof with a different approach if available
    if command -v lsof >/dev/null 2>&1; then
        PID=$(lsof -i :$PORT -t 2>/dev/null)
    fi
fi

if [ -z "$PID" ]; then
    echo -e "${RED}✗ MCP Registry Server is not running on $HOST:$PORT${NC}"
    echo "You can start it with: ./start_registry_server.sh"
    exit 1
else
    echo -e "${GREEN}✓ MCP Registry Server is running${NC}"
    echo "  - PID: $PID"
    echo "  - Address: $HOST:$PORT"
    
    # Check if the server is responding to requests
    if curl -s -f -m 5 "http://$HOST:$PORT/health" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Registry server is responding to health checks${NC}"
        
        # Get additional information from the server
        HEALTH_INFO=$(curl -s -f -m 5 "http://$HOST:$PORT/health" 2>/dev/null)
        if [ $? -eq 0 ]; then
            echo "  - Health status: $(echo $HEALTH_INFO | jq -r '.status' 2>/dev/null || echo "unknown")"
            ACTIVE_SERVICES=$(echo $HEALTH_INFO | jq -r '.active_services' 2>/dev/null || echo "unknown")
            echo "  - Active services: $ACTIVE_SERVICES"
        fi
        
        # List registered services
        SERVICES=$(curl -s -f -m 5 "http://$HOST:$PORT/services" 2>/dev/null)
        if [ $? -eq 0 ] && [ -n "$SERVICES" ]; then
            SERVICE_COUNT=$(echo $SERVICES | jq -r '.services | length' 2>/dev/null || echo "0")
            echo "  - Registered services: $SERVICE_COUNT"

            if [ "$SERVICE_COUNT" -gt 0 ]; then
                echo "  - Service list:"

                # Extract and display services in a more readable format
                echo $SERVICES | jq -r '.services[] | "    - \(.id) at \(.host):\(.port) (\(.type))"' 2>/dev/null || echo "    Unable to parse service list"

                # Count specific types of services
                echo "  - Service breakdown:"
                echo $SERVICES | jq -r '.services[] | .type' 2>/dev/null | sort | uniq -c | while read count type; do
                    echo "    - $count $type service(s)"
                done
            fi
        fi
    else
        echo -e "${YELLOW}⚠ Registry server is running but not responding to health checks${NC}"
        echo "  - Process is running but may not be fully operational"
    fi
fi