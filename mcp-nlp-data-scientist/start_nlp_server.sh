#!/bin/bash
# Start NLP Data Scientist MCP Server

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Configuration
PORT=3065
REGISTRY_PORT=3031
HOST="127.0.0.1"

# Activate virtual environment if exists
if [ -d "../ai_agent_env" ]; then
    source ../ai_agent_env/bin/activate
elif [ -d "ai_agent_env" ]; then
    source ai_agent_env/bin/activate
fi

echo "Starting NLP Data Scientist MCP Server on port $PORT..."
echo "Registry: $HOST:$REGISTRY_PORT"

# Start server
python -m mcp_nlp_server.server \
    --transport streamable-http \
    --host "$HOST" \
    --port "$PORT" \
    --register-with-registry \
    --registry-host "$HOST" \
    --registry-port "$REGISTRY_PORT" \
    "$@"
