#!/bin/bash
# Script to stop the Streamlit application on port 8501

echo "Stopping Streamlit application on port 8501..."

# Find and kill the process running on port 8501
PORT=8501
PIDS=$(lsof -t -i:$PORT 2>/dev/null)

if [ ! -z "$PIDS" ]; then
    echo "Found processes running on port $PORT: $PIDS, stopping them..."
    kill $PIDS
    sleep 2
    echo "Streamlit application stopped."
else
    echo "No process found running on port $PORT"
fi