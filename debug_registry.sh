#!/bin/bash
# Script to test registry startup with more debugging

echo "Testing registry startup..."

# Kill any existing registry processes
echo "Killing any existing registry processes..."
pkill -f "start_registry_server" || true
sleep 2

# Check if port is in use
echo "Checking if port 8080 is in use..."
if lsof -i :8080 > /dev/null; then
    echo "Port 8080 is in use:"
    lsof -i :8080
else
    echo "Port 8080 is free"
fi

# Activate virtual environment
source /root/qwen_test/ai_agent/ai_agent_env/bin/activate

# Try to start the registry
echo "Attempting to start registry server..."
cd /root/qwen_test/ai_agent
timeout 10 python -m registry.start_registry_server --host 127.0.0.1 --port 8080 &
REG_PID=$!

# Wait a bit
sleep 3

# Check if the process is running
if ps -p $REG_PID > /dev/null; then
    echo "Registry process $REG_PID is running"
    
    # Check if it's listening on the port
    if lsof -i :8080 | grep LISTEN > /dev/null; then
        echo "Registry is listening on port 8080"
        
        # Test health endpoint
        if curl -s -f -m 5 "http://127.0.0.1:8080/health" > /dev/null 2>&1; then
            echo "SUCCESS: Registry is responding to health checks"
        else
            echo "FAILURE: Registry is not responding to health checks"
        fi
    else
        echo "Registry is not listening on port 8080"
    fi
else
    echo "Registry process $REG_PID is not running"
    echo "Checking for error messages:"
    # Since the process ran in foreground, we saw the error already
fi

# Clean up
pkill -f "start_registry_server" || true
sleep 1

echo "Test completed."