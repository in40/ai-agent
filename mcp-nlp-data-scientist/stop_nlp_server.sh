#!/bin/bash
# Stop NLP Data Scientist MCP Server

PORT=3065

echo "Stopping NLP Data Scientist MCP Server on port $PORT..."

# Find and kill process on port 3065
PID=$(lsof -ti:$PORT 2>/dev/null)

if [ -n "$PID" ]; then
    echo "Found process: $PID"
    kill $PID
    sleep 2
    
    # Force kill if still running
    if kill -0 $PID 2>/dev/null; then
        echo "Force killing..."
        kill -9 $PID
    fi
    
    echo "NLP Data Scientist MCP Server stopped"
else
    echo "No process found on port $PORT"
fi
