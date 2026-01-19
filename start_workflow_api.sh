#!/bin/bash
# Script to start the Workflow API server

echo "Starting Workflow API server on port 5001..."

# Navigate to the react_editor directory and start the workflow API server
cd /root/qwen_test/ai_agent/gui/react_editor

# Activate the virtual environment and start the server
source ../../ai_agent_env/bin/activate
python3 workflow_api.py > workflow_api.log 2>&1 &

# Store the process ID
API_PID=$!

# Wait a moment for the server to start
sleep 3

# Check if the server is running
if kill -0 $API_PID 2>/dev/null; then
    echo "Workflow API server started successfully with PID: $API_PID"
    echo "Access the API at: http://localhost:5001/api/workflow/current"
    echo "Log file: /root/qwen_test/ai_agent/gui/react_editor/workflow_api.log"
else
    echo "ERROR: Workflow API server failed to start"
    exit 1
fi