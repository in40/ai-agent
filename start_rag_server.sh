#!/bin/bash
# Script to start the RAG MCP server

echo "Starting RAG MCP server on port 8091..."

# Activate the virtual environment if it exists
if [ -f "ai_agent_env/bin/activate" ]; then
    source ai_agent_env/bin/activate
fi

# Start the RAG MCP server in the background
nohup python -m rag_component.rag_mcp_server --host 127.0.0.1 --port 8091 --registry-url http://127.0.0.1:8080 > rag_server.log 2>&1 &

# Save the PID of the RAG server
RAG_SERVER_PID=$!

echo "RAG MCP server started with PID: $RAG_SERVER_PID"

# Wait a moment for the server to start
sleep 3

# Check if the server is running
if ps -p $RAG_SERVER_PID > /dev/null; then
    echo "RAG MCP server is running on port 8091"
    echo "Check rag_server.log for server output"
else
    echo "ERROR: RAG MCP server failed to start"
    exit 1
fi