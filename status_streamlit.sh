#!/bin/bash
# Script to check the status of the Streamlit application on port 8501

PORT=8501
PIDS=$(lsof -t -i:$PORT 2>/dev/null)

if [ ! -z "$PIDS" ]; then
    echo "Streamlit application is running on port $PORT (PID: $PIDS)"
    # Show more details about the process
    ps -p $PIDS -o pid,ppid,cmd,%mem,%cpu
else
    echo "Streamlit application is NOT running on port $PORT"
fi