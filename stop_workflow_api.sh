#!/bin/bash
# Script to stop the Workflow API server

echo "Stopping Workflow API server on port 5001..."

# Find the process running on port 5001
PID=$(lsof -t -i:5001 2>/dev/null)

if [ ! -z "$PID" ]; then
    echo "Found Workflow API server process $PID, stopping it..."
    kill $PID
    
    # Wait a moment to allow graceful shutdown
    sleep 2
    
    # Check if process is still running and force kill if necessary
    if kill -0 $PID 2>/dev/null; then
        echo "Process still running, force stopping..."
        kill -9 $PID 2>/dev/null || true
        echo "Workflow API server force stopped."
    else
        echo "Workflow API server stopped successfully."
    fi
else
    echo "No Workflow API server process found on port 5001"
fi

echo "Done."