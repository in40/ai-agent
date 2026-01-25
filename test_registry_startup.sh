#!/bin/bash
# Test script to verify that the MCP registry starts reliably

set -e  # Exit on any error

echo "Testing MCP Registry startup reliability..."

# Clean up any existing registry processes
echo "Cleaning up existing registry processes..."
pkill -f "start_registry_server" || true
sleep 2

# Test 1: Start the registry using the improved start_all_services.sh approach
echo "Test 1: Starting registry via start_all_services.sh approach..."
cd /root/qwen_test/ai_agent

# Activate virtual environment
source ai_agent_env/bin/activate

# Start registry in background
nohup python -m registry.start_registry_server --host 127.0.0.1 --port 8080 > test_registry.log 2>&1 &
REGISTRY_PID=$!

# Wait a moment for startup
sleep 5

# Check if the process is running
if ps -p $REGISTRY_PID > /dev/null; then
    echo "✓ Registry process is running with PID: $REGISTRY_PID"
    
    # Test health endpoint
    if curl -s -f -m 10 "http://127.0.0.1:8080/health" > /dev/null 2>&1; then
        echo "✓ Registry server is responding to health checks"
        
        # Get health info
        HEALTH_INFO=$(curl -s -f -m 5 "http://127.0.0.1:8080/health" 2>/dev/null)
        STATUS=$(echo $HEALTH_INFO | python -c "import sys, json; print(json.load(sys.stdin)['status'])" 2>/dev/null || echo "unknown")
        ACTIVE_SERVICES=$(echo $HEALTH_INFO | python -c "import sys, json; print(json.load(sys.stdin)['active_services'])" 2>/dev/null || echo "unknown")
        
        echo "  - Health status: $STATUS"
        echo "  - Active services: $ACTIVE_SERVICES"
    else
        echo "✗ Registry server is not responding to health checks"
        echo "Last 10 lines of test_registry.log:"
        tail -n 10 test_registry.log
        kill $REGISTRY_PID || true
        exit 1
    fi
else
    echo "✗ Registry process is not running"
    echo "Contents of test_registry.log:"
    cat test_registry.log
    exit 1
fi

# Test 2: Test the new retry utility
echo ""
echo "Test 2: Testing the new start_registry_with_retry.py utility..."

# Kill existing registry
kill $REGISTRY_PID || true
sleep 2

# Start using the new utility
python utils/start_registry_with_retry.py --port 8080 &
UTILITY_PID=$!

# Wait for startup
sleep 5

# Check if the process is running
if ps -p $UTILITY_PID > /dev/null; then
    echo "✓ Registry started via utility is running with PID: $UTILITY_PID"
    
    # Test health endpoint
    if curl -s -f -m 10 "http://127.0.0.1:8080/health" > /dev/null 2>&1; then
        echo "✓ Registry server (via utility) is responding to health checks"
    else
        echo "✗ Registry server (via utility) is not responding to health checks"
        kill $UTILITY_PID || true
        exit 1
    fi
else
    echo "✗ Registry process (via utility) is not running"
    exit 1
fi

# Clean up
kill $UTILITY_PID || true
sleep 1

echo ""
echo "✓ All registry startup tests passed!"
echo "✓ MCP Registry is now starting reliably"