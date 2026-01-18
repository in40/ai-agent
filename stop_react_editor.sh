#!/bin/bash
# Script to stop the React development server on port 3000

echo "Stopping React development server on port 3000..."

# Find and kill the process running on port 3000
PORT=3000
PID=$(lsof -t -i:$PORT 2>/dev/null)

if [ ! -z "$PID" ]; then
    echo "Found process $PID running on port $PORT, stopping it..."
    kill $PID
    echo "React development server stopped."
else
    echo "No process found running on port $PORT"
fi