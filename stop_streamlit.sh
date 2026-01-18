#!/bin/bash
# Script to stop the Streamlit application on port 8501

echo "Stopping Streamlit application on port 8501..."

# Find and kill the process running on port 8501
PORT=8501
PID=$(lsof -t -i:$PORT 2>/dev/null)

if [ ! -z "$PID" ]; then
    echo "Found process $PID running on port $PORT, stopping it..."
    kill $PID
    echo "Streamlit application stopped."
else
    echo "No process found running on port $PORT"
fi