#!/bin/bash
# Script to stop the RAG MCP server

echo "Stopping RAG MCP server on port 8091..."

# Find and kill the RAG server process
PORT=8091
PID=$(lsof -t -i:$PORT 2>/dev/null)

if [ ! -z "$PID" ]; then
    echo "Found RAG server process $PID, stopping it..."
    kill $PID
    
    # Wait a moment for the process to stop
    sleep 2
    
    # Double check if the process is still running
    if ps -p $PID > /dev/null; then
        echo "Process still running, force killing..."
        kill -9 $PID
    fi
    
    echo "RAG MCP server stopped"
else
    echo "No RAG server process found on port $PORT"
fi