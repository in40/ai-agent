#!/bin/bash

# Script to start the MCP server with various options
# Usage: ./start_mcp_server.sh [options]

echo "Starting MCP Server..."

# Default values
TRANSPORT="streamable-http"
HOST="127.0.0.1"
PORT=3030
ENABLE_REGISTRY=false
REGISTER_WITH_REGISTRY=true
REGISTRY_HOST="127.0.0.1"
REGISTRY_PORT=3031
USE_POSTGRES=false
MAX_CONCURRENT_REQUESTS=10

# Parse command line options
while [[ $# -gt 0 ]]; do
  case $1 in
    --transport)
      TRANSPORT="$2"
      shift 2
      ;;
    --host)
      HOST="$2"
      shift 2
      ;;
    --port)
      PORT="$2"
      shift 2
      ;;
    --enable-registry)
      ENABLE_REGISTRY=true
      shift
      ;;
    --register-with-registry)
      REGISTER_WITH_REGISTRY=true
      shift
      ;;
    --registry-host)
      REGISTRY_HOST="$2"
      shift 2
      ;;
    --registry-port)
      REGISTRY_PORT="$2"
      shift 2
      ;;
    --use-postgres)
      USE_POSTGRES=true
      shift
      ;;
    --max-concurrent-requests)
      MAX_CONCURRENT_REQUESTS="$2"
      shift 2
      ;;
    -h|--help)
      echo "Usage: $0 [OPTIONS]"
      echo ""
      echo "Options:"
      echo "  --transport TYPE          Transport type (stdio, http, streamable-http) [default: streamable-http]"
      echo "  --host HOST               Host for HTTP transport [default: 127.0.0.1]"
      echo "  --port PORT               Port for HTTP transport [default: 3030]"
      echo "  --enable-registry         Enable registry functionality"
      echo "  --register-with-registry  Register this server with a registry server"
      echo "  --registry-host HOST      Registry server host [default: 127.0.0.1]"
      echo "  --registry-port PORT      Registry server port [default: 3031]"
      echo "  --use-postgres            Use PostgreSQL for registry storage instead of SQLite"
      echo "  --max-concurrent-requests NUM  Maximum number of concurrent requests [default: 10]"
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

# Build the command
CMD="python -m mcp_std_server.server"

if [ "$TRANSPORT" != "stdio" ]; then
  CMD="$CMD --transport $TRANSPORT"
fi

if [ "$HOST" != "127.0.0.1" ]; then
  CMD="$CMD --host $HOST"
fi

if [ "$PORT" != "3030" ]; then
  CMD="$CMD --port $PORT"
fi

if [ "$ENABLE_REGISTRY" = true ]; then
  CMD="$CMD --enable-registry"
fi

if [ "$REGISTER_WITH_REGISTRY" = true ]; then
  CMD="$CMD --register-with-registry"
fi

if [ "$REGISTRY_HOST" != "127.0.0.1" ]; then
  CMD="$CMD --registry-host $REGISTRY_HOST"
fi

if [ "$REGISTRY_PORT" != "3031" ]; then
  CMD="$CMD --registry-port $REGISTRY_PORT"
fi

if [ "$USE_POSTGRES" = true ]; then
  CMD="$CMD --use-postgres"
fi

if [ "$MAX_CONCURRENT_REQUESTS" != "10" ]; then
  CMD="$CMD --max-concurrent-requests $MAX_CONCURRENT_REQUESTS"
fi

echo "Executing: $CMD"
exec $CMD