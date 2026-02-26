#!/bin/bash
# Document Store MCP Server Shutdown Script

echo "🛑 Stopping Document Store MCP Server..."

# Find and kill the server process
pkill -f "document_store_server.server"

if [ $? -eq 0 ]; then
    echo "✅ Server stopped"
else
    echo "⚠️  Server was not running"
fi
