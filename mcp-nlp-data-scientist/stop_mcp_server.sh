#!/bin/bash

# Script to stop the MCP Server
# Usage: ./stop_mcp_server.sh [options]

echo "Stopping MCP Server..."

# Default values
PORT=3030
HOST="127.0.0.1"

# Parse command line options
while [[ $# -gt 0 ]]; do
  case $1 in
    --port)
      PORT="$2"
      shift 2
      ;;
    --host)
      HOST="$2"
      shift 2
      ;;
    -h|--help)
      echo "Usage: $0 [OPTIONS]"
      echo ""
      echo "Options:"
      echo "  --port PORT               Port of the server to stop [default: 3030]"
      echo "  --host HOST               Host of the server to stop [default: 127.0.0.1]"
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

# Try to send a shutdown request to the server first
echo "Attempting to send shutdown request to http://$HOST:$PORT..."

# For HTTP transports, we can try to send a shutdown request
if curl -X POST -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "id": "shutdown", "method": "shutdown", "params": {}}' \
  "http://$HOST:$PORT/mcp" 2>/dev/null; then
  echo "Shutdown request sent successfully via Streamable HTTP transport"
elif curl -X POST -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "id": "shutdown", "method": "shutdown", "params": {}}' \
  "http://$HOST:$PORT/send" 2>/dev/null; then
  echo "Shutdown request sent successfully via Legacy HTTP transport"
else
  echo "Could not send shutdown request via HTTP, proceeding with process termination..."
fi

# Give the server a moment to shut down gracefully
sleep 2

# Kill any remaining processes running on the specified port
echo "Terminating any remaining processes on port $PORT..."

# Find and kill processes listening on the specified port
if command -v lsof >/dev/null 2>&1; then
  PORT_PIDS=$(lsof -ti:$PORT)
  if [ -n "$PORT_PIDS" ]; then
    echo "Found processes on port $PORT: $PORT_PIDS"
    kill -TERM $PORT_PIDS 2>/dev/null || true
    sleep 2
    # Force kill if still running
    kill -KILL $PORT_PIDS 2>/dev/null || true
    echo "Processes on port $PORT terminated"
  else
    echo "No processes found running on port $PORT"
  fi
elif command -v netstat >/dev/null 2>&1; then
  PORT_PIDS=$(netstat -tulpn 2>/dev/null | grep ":$PORT " | awk '{print $7}' | cut -d'/' -f1)
  if [ -n "$PORT_PIDS" ]; then
    echo "Found processes on port $PORT: $PORT_PIDS"
    kill -TERM $PORT_PIDS 2>/dev/null || true
    sleep 2
    # Force kill if still running
    kill -KILL $PORT_PIDS 2>/dev/null || true
    echo "Processes on port $PORT terminated"
  else
    echo "No processes found running on port $PORT"
  fi
else
  echo "Warning: Neither lsof nor netstat found, unable to identify processes on port $PORT"
  echo "Attempting to kill python processes that might be MCP servers..."
  pkill -f "mcp_std_server.server" 2>/dev/null || true
  sleep 2
  pkill -9 -f "mcp_std_server.server" 2>/dev/null || true
fi

echo "MCP Server on port $PORT should be stopped."