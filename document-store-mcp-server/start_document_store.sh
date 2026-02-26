#!/bin/bash
# Document Store MCP Server Startup Script
# Starts the Document Store server on port 3070

cd /root/qwen/ai_agent/document-store-mcp-server

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Set environment variables
export DOCUMENT_STORE_PORT=${DOCUMENT_STORE_PORT:-3070}
export DOCUMENT_STORE_TRANSPORT=${DOCUMENT_STORE_TRANSPORT:-streamable-http}
export DOCUMENT_STORAGE_PATH=${DOCUMENT_STORAGE_PATH:-/root/qwen/ai_agent/document-store-mcp-server/data}
export REGISTRY_HOST=${REGISTRY_HOST:-127.0.0.1}
export REGISTRY_PORT=${REGISTRY_PORT:-8080}

echo "🚀 Starting Document Store MCP Server..."
echo "   Port: $DOCUMENT_STORE_PORT"
echo "   Transport: $DOCUMENT_STORE_TRANSPORT"
echo "   Storage: $DOCUMENT_STORAGE_PATH"
echo "   Registry: http://$REGISTRY_HOST:$REGISTRY_PORT"
echo ""

# Start server in background
nohup python -m document_store_server.server \
    --transport $DOCUMENT_STORE_TRANSPORT \
    --port $DOCUMENT_STORE_PORT \
    --registry-host $REGISTRY_HOST \
    --registry-port $REGISTRY_PORT > document_store.log 2>&1 &

echo "✅ Server started with PID: $!"
echo "📄 Logs: document_store.log"
