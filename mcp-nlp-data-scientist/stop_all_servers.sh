#!/bin/bash

# Script to stop all MCP and Registry Servers
# Usage: ./stop_all_servers.sh

echo "Stopping all MCP and Registry Servers..."

# Default ports to check
DEFAULT_MCP_PORTS="3030 3032 3033 3034 8000 8080 9000"
DEFAULT_REGISTRY_PORTS="3031 4000 5000"

# Parse command line options
SPECIFIC_PORTS=""
while [[ $# -gt 0 ]]; do
  case $1 in
    --ports)
      SPECIFIC_PORTS="$2"
      shift 2
      ;;
    -h|--help)
      echo "Usage: $0 [OPTIONS]"
      echo ""
      echo "Options:"
      echo "  --ports PORTS             Specific ports to stop (space-separated)"
      echo "  -h, --help               Show this help message"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      echo "Use --help for usage information"
      exit 1
      ;;
  esac
done

# Determine which ports to check
if [ -n "$SPECIFIC_PORTS" ]; then
  PORTS_TO_CHECK="$SPECIFIC_PORTS"
else
  PORTS_TO_CHECK="$DEFAULT_REGISTRY_PORTS $DEFAULT_MCP_PORTS"
fi

echo "Checking ports: $PORTS_TO_CHECK"

# Function to kill processes on a specific port
kill_on_port() {
  local port=$1
  echo "Checking for processes on port $port..."
  
  if command -v lsof >/dev/null 2>&1; then
    PORT_PIDS=$(lsof -ti:$port)
    if [ -n "$PORT_PIDS" ]; then
      echo "Found processes on port $port: $PORT_PIDS"
      # Try graceful shutdown first by killing with TERM
      kill -TERM $PORT_PIDS 2>/dev/null || true
      sleep 2
      # Check if processes are still running and force kill if needed
      REMAINING_PIDS=$(lsof -ti:$port 2>/dev/null)
      if [ -n "$REMAINING_PIDS" ]; then
        echo "Force killing remaining processes on port $port: $REMAINING_PIDS"
        kill -KILL $REMAINING_PIDS 2>/dev/null || true
      fi
      echo "Processes on port $port terminated"
      return 0
    else
      echo "No processes found on port $port"
      return 1
    fi
  elif command -v netstat >/dev/null 2>&1; then
    PORT_PIDS=$(netstat -tulpn 2>/dev/null | grep ":$port " | awk '{print $7}' | cut -d'/' -f1)
    if [ -n "$PORT_PIDS" ]; then
      echo "Found processes on port $port: $PORT_PIDS"
      kill -TERM $PORT_PIDS 2>/dev/null || true
      sleep 2
      # Check if processes are still running and force kill if needed
      REMAINING_PIDS=$(netstat -tulpn 2>/dev/null | grep ":$port " | awk '{print $7}' | cut -d'/' -f1)
      if [ -n "$REMAINING_PIDS" ]; then
        echo "Force killing remaining processes on port $port: $REMAINING_PIDS"
        kill -KILL $REMAINING_PIDS 2>/dev/null || true
      fi
      echo "Processes on port $port terminated"
      return 0
    else
      echo "No processes found on port $port"
      return 1
    fi
  else
    echo "Warning: Neither lsof nor netstat found, unable to identify processes on port $port"
    return 1
  fi
}

# Track how many processes were terminated
TERMINATED_COUNT=0

# Check each port
for port in $PORTS_TO_CHECK; do
  if kill_on_port $port; then
    TERMINATED_COUNT=$((TERMINATED_COUNT + 1))
  fi
done

# Also try to kill any remaining MCP-related processes regardless of port
echo "Terminating any remaining MCP server processes..."
MCP_PROCESSES=$(pgrep -f "mcp_std_server.server" 2>/dev/null)
if [ -n "$MCP_PROCESSES" ]; then
  echo "Found MCP server processes: $MCP_PROCESSES"
  kill -TERM $MCP_PROCESSES 2>/dev/null || true
  sleep 2
  # Force kill any remaining processes
  REMAINING_MCP_PROCESSES=$(pgrep -f "mcp_std_server.server" 2>/dev/null)
  if [ -n "$REMAINING_MCP_PROCESSES" ]; then
    echo "Force killing remaining MCP server processes: $REMAINING_MCP_PROCESSES"
    kill -KILL $REMAINING_MCP_PROCESSES 2>/dev/null || true
  fi
  ADDITIONAL_TERMINATED=$(echo $MCP_PROCESSES | wc -w)
  TERMINATED_COUNT=$((TERMINATED_COUNT + ADDITIONAL_TERMINATED))
else
  echo "No additional MCP server processes found"
fi

echo "All MCP and Registry servers should be stopped."
echo "Terminated $TERMINATED_COUNT processes in total."