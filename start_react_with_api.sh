#!/bin/bash
# Script to start the workflow API server and React app together

echo "Starting Workflow API server..."
cd /root/qwen_test/ai_agent/gui/react_editor

# Start the workflow API server in the background
source ../../ai_agent_env/bin/activate
python3 workflow_api.py > api_server.log 2>&1 &
API_PID=$!
echo "Workflow API server started with PID: $API_PID"

# Wait a moment for the API server to start
sleep 3

# Check if the API server is running
if kill -0 $API_PID 2>/dev/null; then
    echo "Workflow API server is running on port 5001"
else
    echo "ERROR: Workflow API server failed to start"
    exit 1
fi

echo "Starting React app..."
# Start the React app
npm start > react_app.log 2>&1 &

REACT_PID=$!
echo "React app started with PID: $REACT_PID"

# Wait a moment for the React app to start
sleep 5

# Check if the React app is running
if kill -0 $REACT_PID 2>/dev/null; then
    echo "React app is running on port 3000"
    echo "Access the React app at: http://localhost:3000"
    echo "Access the workflow API at: http://localhost:5001/api/workflow/current"
    echo ""
    echo "To stop both services, run: pkill -f 'workflow_api.py\|react-scripts start'"
else
    echo "ERROR: React app failed to start"
    exit 1
fi

# Keep the script running
wait $API_PID $REACT_PID