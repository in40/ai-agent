#!/bin/bash
# Script to stop the LangGraph Studio server on port 8000

echo "Stopping LangGraph Studio server on port 8000..."

# Find and kill the process running on port 8000
PORT=8000
PID=$(lsof -t -i:$PORT 2>/dev/null)

if [ ! -z "$PID" ]; then
    echo "Found process $PID running on port $PORT, stopping it..."
    kill $PID
    echo "LangGraph Studio server stopped."
else
    echo "No process found running on port $PORT"
fi